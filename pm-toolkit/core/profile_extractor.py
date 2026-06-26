import json
import re
from pathlib import Path
from core.profile_schema import ProfileSchema

SYSTEM_PROMPT = """You are a professional profile extraction assistant. Extract structured information from the provided consultant profile source text and return a single valid JSON object.

YOUR CORE JOB:
Read and understand the full source text. Synthesize, prioritize, and rewrite content into clear, impactful consultant-style bullets and paragraphs. You are not a copy-paste tool — you are an intelligent summarizer. The only hard rule: do NOT invent facts not present in the source.

GENERAL RULES:
- Do NOT use first-person language (no "I", "my", "we").
- Do NOT use words: passionate, enthusiast, thrive, committed, driven, dedicated, love, enjoy.
- Do NOT add marketing language or generic filler.
- Profile field: third-person, factual, consultant-style prose. 3–4 sentences. Synthesize the most impressive facts — scale, industries, technologies, leadership scope.
- Bullets must start with a past-tense action verb.
- Bullets must be specific, synthesized, and impactful. Up to 160 characters. Combine related facts into one strong bullet rather than listing weak fragments.
- Technologies list must be deduplicated and use official product names.
- Competencies must be short labels (2–4 words), not sentences.
- If a field has no data, use empty string or empty list.
- Return ONLY the JSON object. No explanation, no markdown fences, no extra text.

EXPERIENCE PRIORITY STRATEGY (critical):
1. MOST RECENT EMPLOYER: Extract in full detail.
   - Include up to 4 named projects (or theme-grouped projects if no explicit names).
   - Each project gets up to 3 bullets — synthesize achievements + responsibilities into rich, specific statements.
   - If the employer has no explicit project names, group activities into 2–4 meaningful named themes.
2. SECOND MOST RECENT EMPLOYER: Include up to 2 projects, up to 2 bullets each.
3. ALL REMAINING EMPLOYERS: Aggregate into a single synthetic entry:
   - employer: "Previous Experience"
   - role: one-line summary of roles held (e.g. "Senior Developer, Tech Lead — multiple clients")
   - date_range: earliest start year to end year of the block
   - employer_bullets: 2–3 bullets synthesizing the most important facts across all remaining employers
   - projects: empty list

PROJECT EXTRACTION RULES:
- If the source explicitly names projects, use those names.
- If no explicit project names exist, group achievements/activities into named themes.
- Every employer entry (except the aggregated "Previous Experience") must have at least 2 projects.
- Never leave projects empty if achievements or activities are present.

STRICT LIMITS:
  * competencies: max 8 items
  * technologies: max 15 items, deduplicated
  * methodologies: max 5 items
  * education: max 2 items
  * certifications: max 3 items
  * experience entries: exactly 3 (most recent, second most recent, aggregated previous)
  * employer_bullets: max 2 for the top 2 entries; 2–3 for the aggregated entry
  * projects for entry 1: max 4
  * projects for entry 2: max 2
  * bullets per project: max 3 for entry 1; max 2 for entry 2
  * role_subtitle: short role label only, max 5 words

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
      "employer_bullets": ["string"],
      "projects": [
        {
          "project_name": "string",
          "date_range": "string",
          "bullets": ["string"]
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
