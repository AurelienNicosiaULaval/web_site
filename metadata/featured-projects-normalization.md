# Featured Projects Normalization Audit

Date: 2026-07-07

Scope: decision document only. This audit evaluates the public surface of the eight featured repositories listed in the GitHub profile and Research Lab page. It does not modify those repositories, their README files, code, licenses, DOI records, GitHub Pages URLs, names, topics, homepages, visibility settings or archive status.

## Executive Summary

The eight featured projects are now coherently connected through the GitHub profile, the Research Lab page and the README ecosystem boxes added in PR 4. The public ecosystem is broadly consistent: flagship software, reproducible research materials, pedagogical datasets and emerging work are distinguishable.

No urgent correction is required before future repository-specific work. The next step should be a small sequence of independent pull requests, one repository at a time, focused on normalizing README structure, citation visibility, documentation links and badges without changing scientific claims.

Recommendation levels used in this document:

- `no_action`
- `minor_readme_update`
- `documentation_update`
- `citation_or_badge_review`
- `human_decision_needed`

No automatic action is recommended.

## Comparative Table

| Repository | Current GitHub description | Topics | Homepage | README ecosystem box | Installation | Minimal example | Citation | Visible license | Maturity | Recommended level |
|---|---|---|---|---|---|---|---|---|---|---|
| `GLBFP` | This package provides functions for estimating densities using the General Linear Blend Frequency Polygon (GLBFP) approach. It includes tools for estimating densities at specific points and across datasets, as well as visualization tools for one and two-dimensional data. | none | none | yes | yes | yes | yes, README and `CITATION.cff` | yes, GitHub detects GPL-3.0 | mature R package | `minor_readme_update` |
| `ggcircular` | A ggplot2 extension for circular, axial and directional data. | `circular-statistics`, `data-visualization`, `ggplot2`, `r`, `directional-data` | `https://aureliennicosiaulaval.github.io/ggcircular/` | yes | yes | yes | not clearly visible | yes, license file present | young CRAN package | `citation_or_badge_review` |
| `CircularRegression` | CircularRegression is an R package developed for fitting circular-linear regression models, designed to handle directional data such as angles and distances, particularly useful in trajectory analysis and movement ecology. | none | none | yes | yes | partial | not clearly visible | not detected at repository root by GitHub | established R package | `citation_or_badge_review` |
| `Validation-SSF` | Code and analyses for a multi-criteria generative validation framework for step selection functions (SSF and iSSA), including simulations, empirical analysis, and supplementary sensitivity analyses. | `animal-movement`, `ecological-modelling`, `issa`, `methods-in-ecology-and-evolution`, `movement-ecology`, `r`, `simulation-framework`, `spatial-analysis`, `wasserstein-distance`, `generative-validation`, `step-selection-functions` | `https://doi.org/10.5281/zenodo.19485572` | yes | dependencies only | no | DOI badge and `CITATION.cff` | yes, GitHub detects MIT | reproducible research repository | `minor_readme_update` |
| `gmov` | R package for generative validation and diagnostics of SSF and iSSF movement models. | `hidden-markov-models`, `movement-ecology`, `r`, `r-package`, `reproducible-research`, `simulation`, `step-selection-functions` | `https://aureliennicosiaulaval.github.io/gmov/` | yes | yes | yes | `CITATION.cff`, but no clear README citation section | yes, license file present | research package | `citation_or_badge_review` |
| `donnees-bleues` | Plateforme pédagogique ouverte de jeux de données québécois pour la statistique et la science des données | none | `https://aureliennicosiaulaval.github.io/donnees-bleues/` | yes | yes | partial | not clearly visible | not detected at repository root by GitHub | pedagogical data platform | `minor_readme_update` |
| `tutorizeR` | Convert R Markdown and Quarto documents into interactive learnr tutorials with exercises, solutions, and optional quizzes. | `learnr-tutorial`, `quarto` | none | yes | yes | workflow example | DOI badge and `CITATION.cff`, but no clear README citation section | yes, license file present | CRAN teaching package | `citation_or_badge_review` |
| `contextR` | Emerging R package for contextual interpretation of statistical analyses. | `computational-statistics`, `r`, `r-package`, `reproducible-research`, `statistical-interpretation`, `statistics` | none | yes | yes | yes | not clearly visible | yes, license file present | emerging package | `human_decision_needed` |

## Detailed Notes

### `GLBFP`

Current status:

- GitHub description is scientifically aligned with the Research Lab.
- README includes badges, installation, quick start, documentation, references, citation and the Research Lab ecosystem box.
- GitHub does not currently list topics or a homepage.
- GitHub detects a GPL-3.0 license and the repository has a visible citation file.

Assessment:

`GLBFP` has the strongest public package surface among the featured projects. The main normalization gap is metadata discoverability, not README content.

Provisional recommendation:

`minor_readme_update`

Minimal future actions, only after validation:

- Consider adding a homepage in GitHub metadata if the pkgdown site is intended to remain public.
- Consider adding topics aligned with density estimation, R packages and computational statistics.
- Keep the current mature package framing, because it is supported by README structure, citation and package documentation.

### `ggcircular`

Current status:

- GitHub description, topics and homepage are coherent.
- README includes badges, installation, quick start, design principles, documentation link and the Research Lab ecosystem box.
- A license file is visible.
- Citation is not clearly visible in the README and no root `CITATION.cff` was detected.

Assessment:

The repository reads as a young but well-documented CRAN package. Its current lifecycle badge already signals caution. The main missing element is citation guidance.

Provisional recommendation:

`citation_or_badge_review`

Minimal future actions, only after validation:

- Add a short citation section or `CITATION.cff` if citation is needed.
- Keep the existing lifecycle signal so the project is not over-presented as fully mature.
- Avoid expanding cross-links beyond the existing circular-statistics ecosystem links.

### `CircularRegression`

Current status:

- GitHub description is consistent with the Research Lab and profile README.
- README includes installation and the Research Lab ecosystem box.
- README is concise, but examples, citation and license visibility are less explicit than in the more normalized package repositories.
- GitHub does not currently detect a root license.

Assessment:

The project is established as an R package, but the public repository surface is less standardized than `GLBFP` or `ggcircular`.

Provisional recommendation:

`citation_or_badge_review`

Minimal future actions, only after validation:

- Add or clarify a minimal example if not already covered elsewhere.
- Add citation guidance if the package has a preferred citation.
- Review license visibility before any public package-surface normalization.
- Consider whether GitHub topics should be added later, but only as a separate metadata action.

### `Validation-SSF`

Current status:

- GitHub description clearly frames the repository as code and analyses for a generative validation framework.
- README includes a DOI badge, repository structure, dependencies and the Research Lab ecosystem box.
- GitHub homepage points to a Zenodo DOI.
- The repository has a license and `CITATION.cff`.

Assessment:

This should remain framed as reproducible research material, not as a mature R package. The current description is appropriately cautious.

Provisional recommendation:

`minor_readme_update`

Minimal future actions, only after validation:

- Keep the repository out of package-normalization language.
- If useful, add a short "How to reproduce" or "Execution overview" section, not an installation section that suggests package maturity.
- Keep citation and DOI information stable.

### `gmov`

Current status:

- GitHub metadata is coherent with the Research Lab.
- README includes installation, minimal example, vignette, relationship to `amt`, limitations, roadmap, license and the Research Lab ecosystem box.
- GitHub homepage points to the pkgdown site.
- Citation file exists, but citation instructions are not clearly surfaced in the README.

Assessment:

`gmov` can be treated as a research package, but its README already signals limitations and roadmap. That caution should remain.

Provisional recommendation:

`citation_or_badge_review`

Minimal future actions, only after validation:

- Add a short citation section if citation is expected.
- Review whether a status or lifecycle badge would help signal development maturity.
- Keep the package framing cautious and avoid claiming general validation guarantees.

### `donnees-bleues`

Current status:

- GitHub description and homepage are coherent with the Research Lab.
- README is mainly in French and includes goals, repository structure, included datasets, minimal installation and GitHub Pages publication information.
- Research Lab ecosystem box is present.
- GitHub does not detect a root license.
- No citation guidance was detected.

Assessment:

The repository is correctly positioned as a pedagogical data platform centered on Québec datasets. It should not be normalized as an R package unless the repository structure and user-facing documentation justify that framing.

Provisional recommendation:

`minor_readme_update`

Minimal future actions, only after validation:

- Clarify citation or attribution expectations for datasets and generated pages.
- Review license visibility, especially because teaching datasets may have provenance constraints.
- Keep the public framing centered on pedagogy, Québec data and reproducible teaching.

### `tutorizeR`

Current status:

- GitHub description is coherent with the profile and Research Lab.
- README includes DOI and check badges, installation, an end-to-end workflow and the Research Lab ecosystem box.
- `CITATION.cff` and a license file are present.
- GitHub homepage is currently empty, although the package is public and pedagogically central.

Assessment:

The repository is mature enough to remain a featured pedagogical software project. The main normalization question is whether citation and documentation links should be surfaced more directly.

Provisional recommendation:

`citation_or_badge_review`

Minimal future actions, only after validation:

- Add a short citation section if preferred citation should be visible in the README.
- Consider whether a documentation or package page should be used as GitHub homepage.
- Keep the framing focused on `learnr`, Quarto and teaching workflows.

### `contextR`

Current status:

- GitHub description explicitly says "Emerging R package".
- Topics, README and Research Lab wording are coherent with emerging status.
- README includes badges, installation, quick start, backend information, reproducibility checks and the Research Lab ecosystem box.
- README does not link to the sensitive LLM prototype repository.
- Citation is not clearly visible.

Assessment:

`contextR` is coherent but should remain cautiously framed. Any normalization should avoid implying mature production status or linking to related sensitive prototypes.

Provisional recommendation:

`human_decision_needed`

Minimal future actions, only after validation:

- Decide whether a citation section is appropriate now or later.
- Keep "emerging project" wording in the Research Lab, README and GitHub metadata.
- Do not add links to sensitive or precursor repositories unless Aurélien explicitly approves the relationship.

## Minimal Recommendations

Recommended future work should be split into separate pull requests by repository.

- `GLBFP`: metadata/homepage and topics review, if desired.
- `ggcircular`: citation guidance review.
- `CircularRegression`: README example, citation and license visibility review.
- `Validation-SSF`: reproducibility instructions review, while preserving research-material framing.
- `gmov`: citation and maturity-signal review.
- `donnees-bleues`: attribution, provenance and license visibility review.
- `tutorizeR`: citation and documentation-link review.
- `contextR`: human decision on citation and public maturity wording before any expansion.

## Risks

- Over-normalizing all repositories in the same way could make research compendia look like mature R packages.
- Adding badges indiscriminately can imply unsupported maturity, release status or automated quality guarantees.
- Adding citation text without checking DOI or manuscript status could create unstable citation guidance.
- Adding cross-links to sensitive prototypes would contradict `metadata/sensitive-repositories-review.md`.
- Changing license visibility should never be done automatically.
- `contextR` must remain emerging until Aurélien decides otherwise.

## Recommended Future PR Order

1. `GLBFP`: small metadata and README polish review, because it is the most mature featured package.
2. `ggcircular`: citation guidance and badge consistency review.
3. `CircularRegression`: README structure, minimal example, citation and license visibility review.
4. `tutorizeR`: citation and documentation-link review for pedagogical software.
5. `donnees-bleues`: attribution, provenance and license visibility review for teaching datasets.
6. `Validation-SSF`: reproducibility instructions review, keeping repository type explicit.
7. `gmov`: citation and lifecycle/maturity signal review.
8. `contextR`: human decision first, then a cautious README-only normalization if approved.

## Checklist Before Any Future Repository Modification

Before any future PR in a featured repository, verify:

- Aurélien has approved the exact repository and scope.
- Only one repository is modified per PR unless explicitly approved.
- The repository name is unchanged.
- No visibility or archive setting is changed.
- No license file or license metadata is modified without explicit validation.
- No DOI or citation target is changed without explicit validation.
- No GitHub Pages URL is changed.
- No sensitive or private repository is linked.
- `GLBFP_OS` is not linked.
- No link is added to sensitive LLM prototype repositories.
- The repository type remains clear: package, reproducible research material, teaching dataset, pedagogical software or emerging project.
- README wording does not overstate maturity, validation, classroom evidence or production readiness.
- Link checker updates are made only if the new public link is intended to be monitored.

## Scope Reminder

This document is an audit and planning artifact. It does not create any pull request in the eight featured repositories and does not apply any automatic normalization.
