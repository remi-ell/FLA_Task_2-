"""Rebuild docs/diagrams/*, docs/automata.json and the browser demo docs/index.html.
Needs Graphviz (`dot`) on PATH."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from automata_validators.validators import (APPLICATIONS, DATE_LEAP_DFA,  # noqa: E402
                                            DATE_SHAPE_DFA, DATE_VALUE_DFA, MOB_EDGE,
                                            MOBILE_DFA, MOBILE_NFA, PLATE_DFA)

OUT = ROOT / "docs" / "diagrams"
OUT.mkdir(parents=True, exist_ok=True)
DATE_EDGE = {"SL": "/"}

DIAGRAMS = {
    "plate_dfa": PLATE_DFA.to_dot(),
    "mobile_nfa": MOBILE_NFA.to_dot(edge_names=MOB_EDGE),
    "mobile_dfa": MOBILE_DFA.to_dot(edge_names=MOB_EDGE),
    "date_shape_dfa": DATE_SHAPE_DFA.to_dot(edge_names=DATE_EDGE),
    "date_value_dfa": DATE_VALUE_DFA.to_dot(),
    "date_leap_dfa": DATE_LEAP_DFA.to_dot(),
}

# the mobile classes split the digits; print the merged ranges a reader expects
MOB_LABELS = {'"0, 1, 9, 6-8, 2-5"': '"0-9"', '"0-1, 9, 6-8, 2-5"': '"0-9"',
              '"9, 6-8"': '"6-9"', '"0, 9, 6-8, 2-5"': '"0, 2-9"', '"0-1, 2-5"': '"0-5"'}
for key in ("mobile_nfa", "mobile_dfa"):
    for old, new in MOB_LABELS.items():
        DIAGRAMS[key] = DIAGRAMS[key].replace(f"label={old}", f"label={new}")

for name, dot in DIAGRAMS.items():
    (OUT / f"{name}.dot").write_text(dot, encoding="utf-8")
    subprocess.run(["dot", "-Tsvg", "-o", str(OUT / f"{name}.svg")], input=dot.encode(), check=True)
    subprocess.run(["dot", "-Gdpi=170", "-Tpng", "-o", str(OUT / f"{name}.png")],
                   input=dot.encode(), check=True)
    print("wrote", name)

export = {}
for key, app in APPLICATIONS.items():
    d = app["dfa"]
    export[key] = {"title": app["title"], "name": d.name, "start": d.start,
                   "accepting": sorted(d.accepting), "alphabet": d.alphabet,
                   "delta": {f"{p}|{a}": q for (p, a), q in d.delta.items()},
                   "examples": {"accept": app["accept"], "reject": app["reject"]},
                   "states": d.size()}
(ROOT / "docs" / "automata.json").write_text(json.dumps(export, indent=1), encoding="utf-8")
print("wrote docs/automata.json")

svgs = {}
for key, fname in {"plate": "plate_dfa", "mobile": "mobile_dfa", "date": "date_leap_dfa"}.items():
    text = (OUT / f"{fname}.svg").read_text(encoding="utf-8")
    svgs[key] = text[text.index("<svg"):]
page = (ROOT / "tools" / "demo_template.html").read_text(encoding="utf-8")
page = page.replace("__JSON__", json.dumps(export)).replace("__SVG__", json.dumps(svgs))
(ROOT / "docs" / "index.html").write_text(page, encoding="utf-8")
print("wrote docs/index.html")
