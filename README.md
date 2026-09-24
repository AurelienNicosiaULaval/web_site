# Site Quarto - Aurélien Nicosia (Université Laval)

[English version ↓](#english-version)

## Description (FR)

Site personnel construit avec Quarto et déployé via GitHub Pages. Il organise des contenus d'enseignement, de recherche et de ressources dans un format reproductible et maintenable.

- URL du site: https://aureliennicosiaulaval.github.io/web_site/
- Navigation (Quarto): Accueil, Enseignement, Recherche, Projets ouverts, Packages R, Innovation Pédagogique, Autres, À propos, CV, Langue (EN).
- Thème: `cosmo` + CSS personnalisé.
- Déploiement automatisé: GitHub Pages à partir du dossier `docs/` de la branche `main`.

### CV académiques et publication

Les pages `cv/index.qmd` et `en/cv/index.qmd` sont les sources des versions HTML et PDF. Les références dans `_includes/` sont communes aux deux CV et aux pages Recherche. Les PDF publics utilisent uniquement les coordonnées professionnelles.

Après une modification du CV ou des références, avec Quarto et LuaLaTeX disponibles :

```bash
bash scripts/build-cv.sh
quarto render --to html
python3 scripts/check-links.py metadata/link-check.yml
```

Vérifier les deux PDF, les liens de téléchargement et les pages françaises et anglaises avant de publier `docs/` sur `main`. Les fichiers PDF datés du 24 septembre 2026 sont inclus dans le dépôt pour permettre le déploiement sans compilation LaTeX.

### Prévisualiser en local
```bash
quarto preview
```

### Structure
- Pages Quarto: `index.qmd`, `enseignement.qmd`, `recherche.qmd`, `innovation.qmd`, `ressources.qmd`, `a-propos.qmd`
- Projets ouverts: `research-lab.qmd` (adresse conservée)
- CV: `cv/index.qmd`
- Version anglaise: `en/index.qmd`
- Assets: `assets/logo.svg`, `assets/custom.css`, `assets/language-switch.js`
- Output dir: `docs/`

---

## English Version
<a name="english-version"></a>

## Description (EN)

Personal website built with Quarto and deployed via GitHub Pages. It provides a simple, reproducible structure for teaching, research, resources, and an English entry point.

- Site URL: https://aureliennicosiaulaval.github.io/web_site/
- Navigation (Quarto): Home, Teaching, Research, Open projects, R packages, Pedagogical Innovation, Other, About, CV, Language (EN).
- Theme: `cosmo` + custom CSS.
- Automated deployment: GitHub Pages from the `docs/` directory on the `main` branch.

### Academic CVs and publishing

`cv/index.qmd` and `en/cv/index.qmd` are the HTML and PDF sources. References in `_includes/` are shared by both CVs and research pages. Public PDFs contain professional contact details only.

After editing a CV or its references, run `bash scripts/build-cv.sh` with Quarto and LuaLaTeX available, then `quarto render --to html`. Review both PDFs and their download links before publishing `docs/` on `main`.

### Preview locally
```bash
quarto preview
```

### Structure
- Quarto pages: `index.qmd`, `enseignement.qmd`, `recherche.qmd`, `innovation.qmd`, `ressources.qmd`, `a-propos.qmd`
- Open projects: `research-lab.qmd` (existing URL retained)
- CV: `cv/index.qmd`
- English version: `en/index.qmd`
- Assets: `assets/logo.svg`, `assets/custom.css`, `assets/language-switch.js`
- Output dir: `docs/`

---
© 2025 Aurélien — Université Laval
