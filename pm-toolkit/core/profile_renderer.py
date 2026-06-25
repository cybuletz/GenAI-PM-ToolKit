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

    def _build_projects_block(self, experience: list) -> list:
        """
        Returns a list of (text, bold, use_sz) tuples instead of a flat string,
        so the renderer can apply exact per-line formatting matching the reference PPTX.

        Format (mirrors manual PPTX exactly):
          Employer - Role / Date     bold, no explicit sz (inherits frame default)
          Project Name               bold, sz=800
          ' bullet text'             normal, sz=800, leading space
          Project Name 2             bold, sz=800
          ' bullet text'             normal, sz=800
          [blank line between employers]
        """
        lines = []  # list of (text, bold, explicit_sz_or_None)
        for i, exp in enumerate(experience):
            if i > 0:
                lines.append(("", False, 800))  # blank separator between employers
            heading = f"{exp.employer} \u2013 {exp.role} / {exp.date_range}"
            lines.append((heading, True, None))  # employer heading: bold, inherit sz
            for proj in exp.projects:
                lines.append((proj.project_name, True, 800))  # project name: bold, sz=800
                for b in proj.bullets:
                    lines.append((f" {b}", False, 800))  # bullet: normal, sz=800, leading space
        return lines

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
        runs = para.runs
        if not runs:
            for t_node in para._p.iter():
                if t_node.tag.endswith("}t") and t_node.text and "{{" in t_node.text:
                    for token, value in replacements.items():
                        t_node.text = t_node.text.replace(token, value)
            return

        combined = "".join(r.text or "" for r in runs)
        if "{{" not in combined:
            return

        for token, value in replacements.items():
            if token not in combined:
                continue
            replaced_in_run = False
            for run in runs:
                if token in (run.text or ""):
                    run.text = run.text.replace(token, value)
                    replaced_in_run = True
                    break
            if not replaced_in_run:
                self._heal_split_token(runs, token, value)
            combined = "".join(r.text or "" for r in runs)

    def _heal_split_token(self, runs, token: str, value: str):
        texts = [r.text or "" for r in runs]
        n = len(texts)
        for start in range(n):
            for end in range(start + 1, n + 1):
                segment = "".join(texts[start:end])
                if token in segment:
                    runs[start].text = segment.replace(token, value)
                    for i in range(start + 1, end):
                        runs[i].text = ""
                    return

    # ------------------------------------------------------------------
    # KEY_PROJECTS: rebuild text frame matching reference PPTX exactly
    # Employer heading: bold, no explicit sz (inherits text frame default)
    # Project name:     bold, sz=800
    # Bullet line:      normal, sz=800, text has leading space
    # Line spacing:     100% (pct:100000), no spcBef
    # ------------------------------------------------------------------

    def _rebuild_projects_block(self, anchor_para, line_specs: list):
        """
        line_specs: list of (text, bold, sz_or_None) from _build_projects_block
        """
        tf_elem = anchor_para._p.getparent()
        existing_paras = tf_elem.findall(qn('a:p'))

        # Capture color and typeface from anchor para first run
        base_color = None
        base_typeface = None
        ref_runs = anchor_para._p.findall('.//' + qn('a:r'))
        if ref_runs:
            rPr = ref_runs[0].find(qn('a:rPr'))
            if rPr is not None:
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

        def _make_p(text: str, bold: bool, sz):
            color_xml = ""
            if base_color:
                color_xml = f'<a:solidFill><a:srgbClr val="{base_color}"/></a:solidFill>'
            sz_xml = f' sz="{sz}"' if sz is not None else ''
            b_xml = ' b="1"' if bold else ' b="0"'
            lat_xml = f'<a:latin typeface="{base_typeface}"/>' if base_typeface else ''
            safe = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return parse_xml(
                f'<a:p xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                f'<a:pPr><a:lnSpc><a:spcPct val="100000"/></a:lnSpc></a:pPr>'
                f'<a:r>'
                f'<a:rPr lang="en-US"{sz_xml}{b_xml} dirty="0">{color_xml}{lat_xml}</a:rPr>'
                f'<a:t>{safe}</a:t>'
                f'</a:r>'
                f'</a:p>'
            )

        prev_p = None
        for (text, bold, sz) in line_specs:
            new_p = _make_p(text, bold=bold, sz=sz)
            if prev_p is None:
                tf_elem.append(new_p)
            else:
                prev_p.addnext(new_p)
            prev_p = new_p
