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
            self._process_shape(shape, replacements, profile)
        prs.save(str(output_path))

    # ------------------------------------------------------------------
    # Shape traversal - recurses into groups
    # ------------------------------------------------------------------

    def _process_shape(self, shape, replacements, profile):
        if shape.shape_type == 6:  # GROUP
            try:
                for child in shape.shapes:
                    self._process_shape(child, replacements, profile)
            except Exception:
                pass
            return
        if shape.has_text_frame:
            self._replace_in_shape(shape, replacements, profile)

    # ------------------------------------------------------------------
    # Build replacement dict
    # ------------------------------------------------------------------

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
                proj_heading = f"  {proj.project_name}"
                lines.append(proj_heading)
                for b in proj.bullets:
                    lines.append(f"  \u2022 {b}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Per-shape replacement
    # ------------------------------------------------------------------

    def _replace_in_shape(self, shape, replacements: dict, profile: ProfileSchema):
        tf = shape.text_frame
        for para in tf.paragraphs:
            via_xml = "".join(
                (t.text or "") for t in para._p.iter() if t.tag.endswith("}t")
            )
            if "{{" not in via_xml:
                continue
            if "{{KEY_PROJECTS}}" in via_xml:
                self._rebuild_projects_block(para, replacements["{{KEY_PROJECTS}}"])
                return
            self._apply_replacements_to_para(para, replacements)

    def _apply_replacements_to_para(self, para, replacements: dict):
        """
        Replace tokens while preserving per-run formatting.
        Strategy:
        - First try to replace token within the run that contains it (ideal: no split).
        - If a token is split across runs, heal those specific runs then replace.
        """
        runs = para.runs
        if not runs:
            # No runs — tokens in bare <a:t> nodes
            for t_node in para._p.iter():
                if t_node.tag.endswith("}t") and t_node.text and "{{" in t_node.text:
                    for token, value in replacements.items():
                        t_node.text = t_node.text.replace(token, value)
            return

        # Build the full text to check if any token is present
        combined = "".join(r.text or "" for r in runs)
        if "{{" not in combined:
            return

        # For each token, try replacing within individual runs first (preserves formatting)
        for token, value in replacements.items():
            if token not in combined:
                continue

            # Check if token lives entirely within a single run
            replaced_in_run = False
            for run in runs:
                if token in (run.text or ""):
                    run.text = run.text.replace(token, value)
                    replaced_in_run = True
                    break

            if not replaced_in_run:
                # Token is split across runs — find the span of runs that together contain it
                # and consolidate just those runs into the first of them
                self._heal_split_token(runs, token, value)

            # Rebuild combined after each replacement
            combined = "".join(r.text or "" for r in runs)

    def _heal_split_token(self, runs, token: str, value: str):
        """
        Find the minimal consecutive run range whose concatenated text contains
        the token, consolidate those runs into the first, then replace.
        """
        texts = [r.text or "" for r in runs]
        n = len(texts)
        for start in range(n):
            for end in range(start + 1, n + 1):
                segment = "".join(texts[start:end])
                if token in segment:
                    new_text = segment.replace(token, value)
                    runs[start].text = new_text
                    for i in range(start + 1, end):
                        runs[i].text = ""
                    return

    # ------------------------------------------------------------------
    # KEY_PROJECTS: rebuild entire text frame
    # ------------------------------------------------------------------

    def _rebuild_projects_block(self, anchor_para, block_text: str):
        tf_elem = anchor_para._p.getparent()
        existing_paras = tf_elem.findall(qn('a:p'))

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

        for p in existing_paras:
            tf_elem.remove(p)

        def _make_p(text: str, bold: bool):
            color_xml = ""
            if base_color:
                color_xml = f'<a:solidFill><a:srgbClr val="{base_color}"/></a:solidFill>'
            sz_xml = f' sz="{base_sz}"' if base_sz else ''
            b_xml = ' b="1"' if bold else ' b="0"'
            lat_xml = f'<a:latin typeface="{base_typeface}"/>' if base_typeface else ''
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
            is_heading = bool(line) and not line.startswith("  ")
            new_p = _make_p(line, bold=is_heading)
            if prev_p is None:
                tf_elem.append(new_p)
            else:
                prev_p.addnext(new_p)
            prev_p = new_p
