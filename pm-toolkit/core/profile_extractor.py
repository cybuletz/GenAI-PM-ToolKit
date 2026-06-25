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
- All bullet points must be factual and concise, max 130 characters each.
- Technologies list must be deduplicated and use official product names.
- Competencies must be short labels, not sentences.
- If a field has no data in the source, use empty string or empty list.
- Return ONLY the JSON object. No explanation, no markdown fences, no extra text.
- STRICT LIMITS — enforce these exactly:
  * competencies: max 8 items
  * technologies: max 20 items, deduplicated
  * methodologies: max 6 items
  * education: max 3 items
  * certifications: max 3 items
  * experience: max 5 employer entries
  * employer_bullets: max 2 per employer
  * projects per employer: max 4
  * bullets per project: max 3 (pick the most impactful only)

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
    """Return clean multi-line text from a cell, stripping blank lines."""
    lines = [p.text.strip() for p in cell.paragraphs if p.text.strip()]
    return "\n".join(lines)


def _extract_docx_text(file_path: Path) -> str:
    """
    Walk a DOCX document emitting text in document order.
    Handles the common CV table pattern where:
      - Column 0 is empty (decorative)
      - Column 1 holds employer name / date (merged across 3 rows)
      - Column 2 holds the full job description (merged across all 3 rows)
    Deduplicates merged cells by tracking their underlying _tc XML element id.
    """
    from docx import Document
    from docx.oxml.ns import qn
    from docx.text.paragraph import Paragraph
    from docx.table import Table

    doc = Document(str(file_path))
    output_lines = []

    # Track which _tc elements have already been emitted globally
    emitted_tc_ids: set = set()

    def emit_cell(cell) -> str | None:
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
                    # If only one part, emit as plain line
                    # If multiple, join with separator so AI can parse columns
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
