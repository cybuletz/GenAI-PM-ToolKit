import json
import copy
from pathlib import Path
from pptx import Presentation
from pptx.util import Pt
from pptx.dml.color import RGBColor
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
            heading = f"{exp.employer} – {exp.role} / {exp.date_range}"
            lines.append(heading)
            for b in exp.employer_bullets:
                lines.append(f"  • {b}")
            for proj in exp.projects:
                lines.append("")
                proj_heading = f"  {proj.project_name} / {proj.date_range}"
                lines.append(proj_heading)
                for b in proj.bullets:
                    lines.append(f"  • {b}")
        return "\n".join(lines)

    def _replace_in_shape(self, shape, replacements: dict, profile: ProfileSchema):
        tf = shape.text_frame
        for para in tf.paragraphs:
            full_text = "".join(run.text for run in para.runs)
            matched_token = None
            for token in replacements:
                if token in full_text:
                    matched_token = token
                    break
            if matched_token is None:
                continue

            if matched_token == "{{KEY_PROJECTS}}":
                self._rebuild_projects_para(para, replacements[matched_token], profile)
            else:
                replacement_value = replacements[matched_token]
                replaced = False
                for run in para.runs:
                    if matched_token in run.text:
                        run.text = run.text.replace(matched_token, replacement_value)
                        replaced = True
                        break
                if not replaced and para.runs:
                    para.runs[0].text = full_text.replace(matched_token, replacement_value)
                    for run in para.runs[1:]:
                        run.text = ""

    def _rebuild_projects_para(self, para, block_text: str, profile: ProfileSchema):
        from pptx.oxml.ns import qn
        from lxml import etree
        import copy

        tf = para._p.getparent()
        existing_paras = tf.findall(qn('a:p'))
        ref_para = existing_paras[0] if existing_paras else para._p

        # Capture base font properties from the first run in the reference paragraph
        base_font_size = None
        base_font_color = None
        base_font_name = None
        try:
            ref_runs = ref_para.findall('.//' + qn('a:r'))
            if ref_runs:
                rPr = ref_runs[0].find(qn('a:rPr'))
                if rPr is not None:
                    sz = rPr.get('sz')
                    if sz:
                        base_font_size = int(sz)
                    solid_fill = rPr.find('.//' + qn('a:solidFill'))
                    if solid_fill is not None:
                        srgb = solid_fill.find(qn('a:srgbClr'))
                        if srgb is not None:
                            base_font_color = srgb.get('val')
                    latin = rPr.find(qn('a:latin'))
                    if latin is not None:
                        base_font_name = latin.get('typeface')
        except Exception:
            pass

        # Remove all existing paragraphs in this text frame except keep one as anchor
        for p in existing_paras[1:]:
            tf.remove(p)

        lines = block_text.split("\n")

        def make_para_xml(text, bold, font_size, font_color, font_name):
            from pptx.oxml import parse_xml
            from pptx.oxml.ns import nsmap
            color_xml = ""
            if font_color:
                color_xml = f'<a:solidFill><a:srgbClr val="{font_color}"/></a:solidFill>'
            sz_xml = f' sz="{font_size}"' if font_size else ''
            bold_xml = ' b="1"' if bold else ' b="0"'
            latin_xml = f'<a:latin typeface="{font_name}"/>' if font_name else ''
            xml_str = (
                f'<a:p xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
                f'<a:r>'
                f'<a:rPr lang="en-US"{sz_xml}{bold_xml} dirty="0">{color_xml}{latin_xml}</a:rPr>'
                f'<a:t>{text}</a:t>'
                f'</a:r>'
                f'</a:p>'
            )
            return parse_xml(xml_str)

        first = True
        for line in lines:
            is_heading = line and not line.startswith("  ")
            is_bullet = line.strip().startswith("•")
            bold = is_heading
            new_p = make_para_xml(
                line,
                bold=bold,
                font_size=base_font_size,
                font_color=base_font_color,
                font_name=base_font_name
            )
            if first:
                tf.replace(ref_para, new_p)
                ref_para = new_p
                first = False
            else:
                ref_para.addnext(new_p)
                ref_para = new_p
