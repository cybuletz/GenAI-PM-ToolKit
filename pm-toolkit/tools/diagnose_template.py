"""Run this script once on your prepared template to verify all tokens
are readable and show exactly how they are stored in XML runs.

Usage:
  cd pm-toolkit
  python tools/diagnose_template.py
"""
from pathlib import Path
from pptx import Presentation
from lxml import etree

TEMPLATE = Path(__file__).parent.parent / "templates" / "base_profile_template.pptx"

EXPECTED_TOKENS = [
    "{{ROLE_TITLE}}", "{{NAME}}", "{{ROLE_SUBTITLE}}",
    "{{COMP_1}}", "{{COMP_2}}", "{{COMP_3}}", "{{COMP_4}}",
    "{{COMP_5}}", "{{COMP_6}}", "{{COMP_7}}", "{{COMP_8}}",
    "{{PROFILE}}", "{{KEY_PROJECTS}}",
    "{{EDUCATION}}", "{{METHODOLOGIES}}", "{{TECHNOLOGIES}}",
]

prs = Presentation(str(TEMPLATE))
slide = prs.slides[0]

found_tokens = set()

print("=" * 70)
print("TEMPLATE TOKEN DIAGNOSTIC")
print("=" * 70)

for shape in slide.shapes:
    if not shape.has_text_frame:
        continue
    for para in shape.text_frame.paragraphs:
        # Read via python-pptx runs
        via_runs = "".join(r.text for r in para.runs)
        # Read via raw XML <a:t> nodes (catches ALL text regardless of split)
        via_xml = "".join((t.text or "") for t in para._p.iter() if t.tag.endswith("}t"))

        if "{{" not in via_xml:
            continue

        print(f"\nShape {shape.shape_id} ({shape.name!r})")
        print(f"  via .runs : {via_runs!r}")
        print(f"  via XML   : {via_xml!r}")
        print(f"  run count : {len(para.runs)}")
        for i, run in enumerate(para.runs):
            print(f"  run[{i}]    : {run.text!r}")

        for token in EXPECTED_TOKENS:
            if token in via_xml:
                found_tokens.add(token)

print("\n" + "=" * 70)
print("TOKENS FOUND IN TEMPLATE:")
for t in EXPECTED_TOKENS:
    status = "OK" if t in found_tokens else "MISSING"
    print(f"  [{status:7s}] {t}")

missing = [t for t in EXPECTED_TOKENS if t not in found_tokens]
if missing:
    print(f"\n  WARNING: {len(missing)} token(s) not found. Check template preparation.")
else:
    print("\n  All tokens present.")
