import json
import re
from pathlib import Path
from core.profile_schema import ProfileSchema

SYSTEM_PROMPT = """You are a professional profile extraction assistant. Extract structured information from the provided consultant profile source text and return it as a single valid JSON object matching the schema below.

RULES:
- Extract ONLY facts explicitly stated in the source text.
- Do NOT infer, invent, or embellish any information.
- Do NOT use first-person language anywhere (no "I", "my", "we").
- Do NOT use words: passionate, enthusiast, thrive, committed, driven, dedicated, love, enjoy.
- Do NOT add marketing language or generic filler.
- Profile field must be written in third-person, factual, consultant-style prose. Max 3 sentences.
- All bullet points must start with a past-tense action verb.
- All bullet points must be factual, specific, and impactful. Max 130 characters each.
- Prioritize bullets that mention: technologies used, scale/numbers, business impact, or concrete outcomes.
- Technologies list must be deduplicated and use official product names.
- Competencies must be short labels, not sentences.
- If a field has no data in the source, use empty string or empty list.
- Return ONLY the JSON object. No explanation, no markdown fences, no extra text.
- STRICT LIMITS — enforce these exactly:
  * competencies: max 8 items
  * technologies: max 15 items, deduplicated
  * methodologies: max 5 items
  * education: max 2 items
  * certifications: max 3 items
  * experience: max 5 employer entries (most recent first)
  * employer_bullets: max 2 per employer (most impactful overview facts)
  * projects per employer: max 3 (most significant only)
  * bullets per project: max 2 (concrete achievements with tech/scale/outcome)
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
            for row in tbl.rows:
                row_parts = []
                for cell in row.cells:
                    text = emit_cell(cell)
                    if text:
                        row_parts.append(text)
                if row_parts:
                    output_lines.append(' || '.join(row_parts))

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
