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
                proj_heading = f"  {proj.project_name} / {proj.date_range}"
                lines.append(proj_heading)
                for b in proj.bullets:
                    lines.append(f"  \u2022 {b}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Shape-level replacement dispatcher
    # ------------------------------------------------------------------

    def _replace_in_shape(self, shape, replacements: dict, profile: ProfileSchema):
        tf = shape.text_frame
        for para in tf.paragraphs:
            # Get full text from ALL <a:t> nodes in this paragraph (catches split runs)
            full_text = self._para_full_text(para)
            if not full_text or "{{" not in full_text:
                continue

            # Check KEY_PROJECTS first (full text-frame rebuild)
            if "{{KEY_PROJECTS}}" in full_text:
                self._rebuild_projects_block(para, replacements["{{KEY_PROJECTS}}"])
                return  # text frame rebuilt, stop processing this shape

            # For all other tokens: apply ALL matching replacements to this paragraph
            # by consolidating runs then doing string replacements
            self._apply_replacements_to_para(para, replacements)

    def _para_full_text(self, para) -> str:
        """Collect text from every <a:t> element in the paragraph XML, not just .runs."""
        return "".join(
            (t.text or "") for t in para._p.iter() if t.tag.endswith("}t")
        )

    def _apply_replacements_to_para(self, para, replacements: dict):
        """
        Strategy:
        1. Consolidate all <a:r> text into the first run (healing run-splits).
        2. Also handle <a:t> nodes that live directly under the paragraph 
           (rare but possible after some editors save).
        3. Apply ALL token replacements in one pass on the consolidated text.
        4. Write the final string back into the first run; blank all others.
        5. For paragraphs where label runs (e.g. 'Education:') must keep their 
           own formatting, only blank the run that CONTAINED the token, not the labels.
        """
        runs = para.runs  # only <a:r> elements

        if not runs:
            # Tokens stored directly in <a:t> under <a:p> (no runs) — rare edge case
            for t_node in para._p.iter():
                if t_node.tag.endswith("}t") and t_node.text and "{{" in t_node.text:
                    new_text = t_node.text
                    for token, value in replacements.items():
                        new_text = new_text.replace(token, value)
                    t_node.text = new_text
            return

        # --- Step 1: Identify which runs contain token fragments ---
        # A token can be split across consecutive runs. We consolidate by scanning
        # the raw XML text nodes and reconstructing per-run ownership.
        
        # Build a list of (run, original_text) pairs
        run_texts = [(r, r.text or "") for r in runs]
        combined = "".join(t for _, t in run_texts)

        if "{{" not in combined:
            return

        # Apply all replacements on the combined string
        new_combined = combined
        for token, value in replacements.items():
            new_combined = new_combined.replace(token, value)

        if new_combined == combined:
            return  # nothing changed

        # --- Step 2: Write back ---
        # Check if this paragraph has "label" runs (bold labels like 'Education:')
        # that should keep their own text. We detect these as runs that don't contain
        # any '{{' fragment and whose text doesn't change in new_combined.
        # 
        # Simple heuristic: if there are only 1-2 runs total, consolidate into run[0].
        # If there are multiple runs AND the non-token runs have important formatting,
        # try to write replacement only into the token-bearing run(s).
        #
        # Full safe approach: consolidate into run[0], preserve run[0]'s formatting.
        runs[0].text = new_combined
        for r in runs[1:]:
            r.text = ""

    # ------------------------------------------------------------------
    # KEY_PROJECTS: rebuild entire text frame
    # ------------------------------------------------------------------

    def _rebuild_projects_block(self, anchor_para, block_text: str):
        tf_elem = anchor_para._p.getparent()
        existing_paras = tf_elem.findall(qn('a:p'))

        # Capture base style from anchor paragraph first <a:r>
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

        # Remove all existing paragraphs from this text frame
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
