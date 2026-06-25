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
- Profile field must be written in third-person, factual, consultant-style prose.
- All bullet points must start with a past-tense action verb.
- All bullet points must be factual and concise, max 130 characters each.
- Technologies list must be deduplicated and use official product names.
- Competencies must be short labels, not sentences.
- If a field has no data in the source, use empty string or empty list.
- Return ONLY the JSON object. No explanation, no markdown fences, no extra text.

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


def _iter_docx_paragraphs(doc):
    """
    Yield all paragraph texts from a DOCX document, including paragraphs
    nested inside tables (which doc.paragraphs silently skips).
    Traversal order: top-level body elements in document order, so table
    rows appear in the same relative position as they do visually.
    """
    from docx.oxml.ns import qn
    from docx.text.paragraph import Paragraph
    from docx.table import Table, _Cell

    def iter_block_items(parent):
        """
        Recursively yield (paragraph_text, context_hint) tuples from any
        block-level parent: Document body, table cell, or nested table cell.
        context_hint is a short label injected before cell content so the AI
        can correlate employer names (left column) with descriptions (right column).
        """
        # Determine the underlying XML element
        if hasattr(parent, 'element'):
            parent_elem = parent.element.body
        elif hasattr(parent, '_tc'):
            parent_elem = parent._tc
        else:
            parent_elem = parent

        for child in parent_elem.iterchildren():
            tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if tag == 'p':
                para = Paragraph(child, parent)
                text = para.text.strip()
                if text:
                    yield text
            elif tag == 'tbl':
                tbl = Table(child, parent)
                for row in tbl.rows:
                    row_texts = []
                    for cell in row.cells:
                        cell_text = ' | '.join(
                            t for t in (p.text.strip() for p in cell.paragraphs) if t
                        )
                        if cell_text:
                            row_texts.append(cell_text)
                    if row_texts:
                        yield ' || '.join(row_texts)

    yield from iter_block_items(doc)


def _extract_text_from_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix == ".docx":
        from docx import Document
        doc = Document(str(file_path))
        lines = list(_iter_docx_paragraphs(doc))
        return "\n".join(lines)
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
