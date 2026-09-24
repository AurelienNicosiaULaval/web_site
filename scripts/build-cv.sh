#!/usr/bin/env bash
# Regenerate the two public CVs before rendering the HTML site.
set -euo pipefail
cd "$(dirname "$0")/.."
quarto render cv/index.qmd --to pdf --output aurelien-nicosia-cv-fr.pdf
mv docs/aurelien-nicosia-cv-fr.pdf cv/aurelien-nicosia-cv-fr.pdf
quarto render en/cv/index.qmd --to pdf --output aurelien-nicosia-cv-en.pdf
mv docs/aurelien-nicosia-cv-en.pdf en/cv/aurelien-nicosia-cv-en.pdf
