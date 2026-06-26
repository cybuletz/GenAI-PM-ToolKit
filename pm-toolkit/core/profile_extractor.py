import json
import re
from pathlib import Path
from core.profile_schema import ProfileSchema

SYSTEM_PROMPT = """You are a professional profile extraction assistant. Extract structured information from the provided consultant profile source text and return a single valid JSON object.

YOUR CORE JOB:
Read and deeply understand the full source text. Your primary goal is to fill the KEY PROJECTS section as richly as possible using every relevant fact from the CURRENT (most recent) employer. You are an intelligent synthesizer, not a copy-paste tool. The only hard rule: do NOT invent facts not present in the source.

GENERAL RULES:
- Do NOT use first-person language (no "I", "my", "we").
- Do NOT use: passionate, enthusiast, thrive, committed, driven, dedicated, love, enjoy.
- Do NOT add marketing language or generic filler.
- Profile field: third-person, factual, consultant-style prose. 3-4 sentences covering full career arc.
- Technologies list: deduplicated, official product names only.
- Competencies: short labels (2-4 words), not sentences.
- If a field has no data, use empty string or empty list.
- Return ONLY the JSON object. No explanation, no markdown fences, no extra text.

FRAME BUDGET:
The KEY PROJECTS section fits ~36 lines of Arial 8pt text (~5,500 chars total).
Structure (headings, project names, blank separators) uses ~12 lines.
This leaves ~24 lines = ~4,000 chars of actual content.
Allocate content as follows:
  - Current employer projects: use as many lines as needed to cover all projects richly
  - Previous experience summary: max 3 lines = ~500 chars (one condensed paragraph)

EXPERIENCE STRATEGY - CRITICAL:

1. CURRENT EMPLOYER (most recent, entry index 0):
   - Extract ALL named projects from the source for this employer.
   - Max 5 projects. If more than 5 exist, pick the 5 most recent or most significant.
   - Each project gets a full content block (paragraph, bullets, or mixed — see formats below).
   - Target 400-600 chars per project content. Write as much as source supports.
   - Use every technology, architecture detail, team size, and outcome mentioned.

2. PREVIOUS EXPERIENCE SUMMARY (entry index 1) — ONE ENTRY ONLY:
   - Combine ALL older employers into a single entry.
   - employer: "Previous Experience"
   - role: summarize roles across all older jobs, e.g. "Java Developer, Team Lead — multiple clients"
   - date_range: earliest year to latest year of all older employers combined
   - employer_bullets: EMPTY LIST (no bullets — use projects instead)
   - projects: exactly ONE project entry:
       project_name: "Career Summary"
       date_range: same as above
       content: ONE condensed paragraph (max 500 chars) summarizing:
         - total years of prior experience
         - industries covered (e.g. healthcare, telecoms, public administration)
         - key roles (developer, team lead, architect)
         - most notable technologies used across all older roles
         - any standout projects or achievements
         Write in third-person past tense. Make it dense and informative.
         Example: "Prior to current role, accumulated 18 years of experience as Java Developer and Team Lead across healthcare, telecommunications, and public administration sectors. Led backend teams on a 6-year trading platform for an investment bank, a SyncML synchronization server in telecoms, a healthcare information system, and an address book server. Core technologies included Java, Spring, Hibernate, MySQL, and various messaging and sync protocols."

CONTENT FORMATS (for current employer projects):

FORMAT A - PARAGRAPH (preferred when source has rich detail):
  3-4 sentences, third-person past tense, no bullets. Target 450-600 chars.
  Combine architecture, team context, technologies, and outcomes.

FORMAT B - BULLETS:
  3-5 lines each starting with \u2022 and a space, separated by \n.
  Each line: past-tense verb + detail. 100-140 chars per line.

FORMAT C - MIXED (paragraph + bullets):
  1-2 prose sentences then \n-separated bullet lines for additional facts.
  Use when you have both a strong narrative and extra distinct facts.

Maximize content length. Do NOT write short when the source has detail.

PROJECT NAMING:
- Use explicit project names from source.
- If no names, group into meaningful themes.
- Every current employer project must have content if the source mentions any detail.

STRICT LIMITS:
  * competencies: max 8
  * technologies: max 15, deduplicated
  * methodologies: max 5
  * education: max 2
  * certifications: max 3
  * experience entries: exactly 2 (current employer + previous experience summary)
  * projects for entry 0 (current): max 5
  * projects for entry 1 (previous summary): exactly 1 ("Career Summary")
  * content per project: max 650 chars (600 for Career Summary)
  * role_subtitle: max 5 words

REQUIRED JSON SCHEMA:
{
  "name": "string",
  "role_title": "string",
  "role_subtitle": "string",
  "profile": "string",
  "competencies": ["string"],
  "education": ["string"],
  "certifications": ["string"],
  "methodologies": ["string"],
  "technologies": ["string"],
  "experience": [
    {
      "employer": "string",
      "role": "string",
      "date_range": "string",
      "employer_bullets": [],
      "projects": [
        {
          "project_name": "string",
          "date_range": "string",
          "content": "string"
        }
      ]
    },
    {
      "employer": "Previous Experience",
      "role": "string",
      "date_range": "string",
      "employer_bullets": [],
      "projects": [
        {
          "project_name": "Career Summary",
          "date_range": "string",
          "content": "string"
        }
      ]
    }
  ]
}"""


def _cell_text(cell) -> str:
    lines = [p.text.strip() for p in cell.paragraphs if p.text.strip()]
    return "\n".join(lines)


def _extract_docx_text(file_path: Path) -> str:
    from docx import Document
    from docx.text.paragraph import Paragraph
    from docx.table import Table

    doc = Document(str(file_path))
    output_lines = []
    emitted_tc_ids: set = set()

    def emit_cell(cell):
        tc_id = id(cell._tc)
        if tc_id in emitted_tc_ids:
            return None
        emitted_tc_ids.add(tc_id)
        return _cell_text(cell) or None

    body = doc.element.body
    for child in body.iterchildren():
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
        if tag == 'p':
            para = Paragraph(child, doc)
            text = para.text.strip()
            if text:
                output_lines.append(text)
        elif tag == 'tbl':
            tbl = Table(child, doc)
            row_texts = []
            for row in tbl.rows:
                row_parts = []
                for cell in row.cells:
                    text = emit_cell(cell)
                    if text:
                        row_parts.append(text)
                if row_parts:
                    row_texts.append(' || '.join(row_parts))
            output_lines.extend(row_texts)

    return "\n".join(output_lines)


def _extract_text_from_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".docx":
        return _extract_docx_text(file_path)
    elif suffix == ".pdf":
        import fitz
        doc = fitz.open(str(file_path))
        pages = [doc.load_page(i).get_text() for i in range(len(doc))]
        return "\n".join(pages)
    elif suffix == ".pptx":
        from pptx import Presentation
        prs = Presentation(str(file_path))
        texts = []
        for slide in prs.slides:
            for shape in slide.shapes:
                if shape.has_text_frame:
                    for para in shape.text_frame.paragraphs:
                        texts.append("".join(run.text for run in para.runs))
        return "\n".join(texts)
    elif suffix == ".txt":
        text = file_path.read_text(encoding="utf-8")
        return re.sub(r'[ \t]+', ' ', text).strip()
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


class ProfileExtractor:
    def __init__(self, copilot_client):
        self.client = copilot_client

    def extract_from_file(self, file_path: Path) -> ProfileSchema:
        raw_text = _extract_text_from_file(file_path)
        return self.extract(raw_text)

    def extract(self, raw_text: str) -> ProfileSchema:
        response = self.client.complete(SYSTEM_PROMPT, raw_text)
        cleaned = re.sub(r'^```(?:json)?\s*', '', response.strip())
        cleaned = re.sub(r'```\s*$', '', cleaned).strip()
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(f"AI returned invalid JSON: {e}\n\nRaw response:\n{response[:500]}")
        try:
            return ProfileSchema(**data)
        except Exception as e:
            raise ValueError(f"Schema validation failed: {e}")
