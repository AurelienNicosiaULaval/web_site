#!/usr/bin/env python3
"""Copier la présentation AMQ validée et ses notices dans les ressources du site."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("dossier", type=Path, help="Dossier local contenant presentation.html et assets/")
args = parser.parse_args()
source = args.dossier.resolve()
site = Path(__file__).resolve().parents[1]
target = site / "presentations/amq-2026"
files = ("presentation.html", "assets/SOURCES-IMAGES.md", "assets/illustration.txt", "assets/cerf-elaphe.jpg")
for name in files:
    if not (source / name).is_file():
        parser.error(f"Fichier requis absent : {source / name}")
html = (source / "presentation.html").read_text()
if 'id="longueur-et-direction"' not in html or 'data-core-slide="49"' not in html:
    parser.error("Le fichier fourni ne correspond pas à la présentation AMQ attendue.")
for name in files:
    output = target / name
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / name, output)
    # GitHub Pages publie docs/ dans ce dépôt. Ces ressources ne sont pas des pages Quarto.
    public = site / "docs/presentations/amq-2026" / name
    public.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(output, public)
print(json.dumps({"presentation": "presentations/amq-2026/presentation.html",
                  "sha256": hashlib.sha256((target / "presentation.html").read_bytes()).hexdigest(),
                  "bytes": (target / "presentation.html").stat().st_size,
                  "notices": list(files[1:3]), "photo": files[3]}, ensure_ascii=False, indent=2))
