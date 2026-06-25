import json
import re
from pathlib import Path
from pptx import Presentation
from pptx.oxml.ns import qn
from pptx.oxml import parse_xml
from core.profile_schema import ProfileSchema


class ProfileRenderer:
    def __init__(self, template_path: Path, spec_path: Path):
        self.template_path = template_path
        self.spec = json.loads(spec_path.read_text(encoding="utf-8"))

    def render(self, profile: ProfileSchema, output_path: Path):
        prs = Presentation(str(self.template_path))
        slide_index = self.spec.get("slide_index", 0)
        slide = prs.slides[slide_index]
        replacements = self._build_replacements(profile)
        for shape in slide.shapes:
            if shape.has_text_frame:
                self._replace_in_shape(shape, replacements, profile)
        prs.save(str(output_path))

    def _build_replacements(self, profile: ProfileSchema) -> dict:
        r = {}
        r["{{ROLE_TITLE}}"] = profile.role_title
        r["{{NAME}}"] = profile.name
        r["{{ROLE_SUBTITLE}}"] = profile.role_subtitle
        r["{{PROFILE}}"] = profile.profile
        for i in range(8):
            token = f"{{{{COMP_{i+1}}}}}"
            value = profile.competencies[i] if i < len(profile.competencies) else ""
            r[token] = value
        r["{{KEY_PROJECTS}}"] = self._build_projects_block(profile.experience)
        r["{{EDUCATION}}"] = " | ".join(profile.education)
        r["{{METHODOLOGIES}}"] = ", ".join(profile.methodologies)
        r["{{TECHNOLOGIES}}"] = ", ".join(profile.technologies)
        return r

    def _build_projects_block(self, experience: list) -> str:
        lines = []
        for i, exp in enumerate(experience):
            if i > 0:
                lines.append("")
            heading = f"{exp.employer} \u2013 {exp.role} / {exp.date_range}"
            lines.append(heading)
            for b in exp.employer_bullets:
                lines.append(f"  \u2022 {b}")
            for proj in exp.projects:
                lines.append("")
                proj_heading = f"  {proj.project_name} / {proj.date_range}"
                lines.append(proj_heading)
                for b in proj.bullets:
                    lines.append(f"  \u2022 {b}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Core replacement: heal run-fragmented tokens before replacing
    # ------------------------------------------------------------------

    def _heal_runs(self, para) -> None:
        """
        PowerPoint often splits a token like {{NAME}} across multiple runs:
          run0.text = '{{', run1.text = 'NAME', run2.text = '}}'
        This merges the text of all runs into run0, blanks the rest,
        preserving run0's formatting.
        Only applied when full_text contains '{{'.
        """
        runs = para.runs
        if len(runs) <= 1:
            return
        full = "".join(r.text for r in runs)
        if '{{' not in full:
            return
        # Consolidate everything into the first run, blank the rest
        runs[0].text = full
        for r in runs[1:]:
            r.text = ""

    def _replace_in_shape(self, shape, replacements: dict, profile: ProfileSchema):
        tf = shape.text_frame
        for para in tf.paragraphs:
            # Step 1: heal any split tokens in this paragraph
            self._heal_runs(para)

            full_text = "".join(run.text for run in para.runs)
            matched_token = None
            for token in replacements:
                if token in full_text:
                    matched_token = token
                    break
            if matched_token is None:
                continue

            if matched_token == "{{KEY_PROJECTS}}":
                self._rebuild_projects_block(para, replacements[matched_token])
            else:
                replacement_value = replacements[matched_token]
                # After healing, the full text is in runs[0]
                for run in para.runs:
                    if matched_token in run.text:
                        run.text = run.text.replace(matched_token, replacement_value)
                        break

    # ------------------------------------------------------------------
    # KEY_PROJECTS: rebuild entire text frame with correct bold/normal
    # ------------------------------------------------------------------

    def _rebuild_projects_block(self, anchor_para, block_text: str):
        """
        Replace the entire text frame that contains the {{KEY_PROJECTS}} token
        with one paragraph per line, bold on employer/project headings.
        Captures font size, color, and typeface from the anchor paragraph's
        first run so the new text inherits the template's base style.
        """
        tf_elem = anchor_para._p.getparent()
        existing_paras = tf_elem.findall(qn('a:p'))

        # Capture base style from anchor paragraph first run
        base_sz = None
        base_color = None
        base_typeface = None
        ref_runs = anchor_para._p.findall('.//' + qn('a:r'))
        if ref_runs:
            rPr = ref_runs[0].find(qn('a:rPr'))
            if rPr is not None:
                sz = rPr.get('sz')
                if sz:
                    base_sz = int(sz)
                sf = rPr.find('.//' + qn('a:solidFill'))
                if sf is not None:
                    srgb = sf.find(qn('a:srgbClr'))
                    if srgb is not None:
                        base_color = srgb.get('val')
                lat = rPr.find(qn('a:latin'))
                if lat is not None:
                    base_typeface = lat.get('typeface')

        # Remove ALL existing paragraphs in this text frame
        for p in existing_paras:
            tf_elem.remove(p)

        def _make_p(text: str, bold: bool) -> object:
            color_xml = ""
            if base_color:
                color_xml = f'<a:solidFill><a:srgbClr val="{base_color}"/></a:solidFill>'
            sz_xml = f' sz="{base_sz}"' if base_sz else ''
            b_xml = ' b="1"' if bold else ' b="0"'
            lat_xml = f'<a:latin typeface="{base_typeface}"/>' if base_typeface else ''
            # Escape XML special chars in text
            safe = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return parse_xml(
                f'<a:p xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                f'<a:r>'
                f'<a:rPr lang="en-US"{sz_xml}{b_xml} dirty="0">{color_xml}{lat_xml}</a:rPr>'
                f'<a:t>{safe}</a:t>'
                f'</a:r>'
                f'</a:p>'
            )

        lines = block_text.split("\n")
        prev_p = None
        for line in lines:
            # Heading = non-indented non-empty line; bullet = starts with '  •'
            is_heading = bool(line) and not line.startswith("  ")
            new_p = _make_p(line, bold=is_heading)
            if prev_p is None:
                tf_elem.append(new_p)
            else:
                prev_p.addnext(new_p)
            prev_p = new_p
