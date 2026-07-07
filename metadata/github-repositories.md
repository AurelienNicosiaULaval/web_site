# GitHub Repository Metadata Plan

This document prepares a coherent update of GitHub repository metadata for the research ecosystem. It does not apply any GitHub metadata changes. Descriptions, topics, and homepages remain unchanged until Aurélien validates the proposed updates and applies them explicitly.

## Strategy

The goal is to make the main repositories easier to understand from GitHub search, repository cards, and profile navigation while preserving all existing repository names, GitHub Pages URLs, DOI records, licenses, visibility settings, and repository status.

The proposed metadata follows four principles:

- use short, sober and professional descriptions;
- reuse existing public GitHub Pages URLs only when they respond publicly;
- mark prototypes and sensitive research materials clearly;
- keep sensitive repositories out of automatic updates.

## Repositories Proposed For Metadata Update

These repositories are public, non-sensitive according to the current plan, and have metadata gaps or metadata that can be made more coherent. Applying these updates should still be done manually after review.

| Repository | Proposed description | Proposed topics | Proposed homepage |
|---|---|---|---|
| `DonutMap` | R package for static and interactive donut maps with sf, ggplot2 and leaflet. | `r`, `r-package`, `data-visualization`, `geospatial`, `sf`, `ggplot2`, `leaflet` | `https://aureliennicosiaulaval.github.io/DonutMap/` |
| `MQT-2101` | Quarto course site for applied data analysis and statistical modelling. | `quarto`, `teaching`, `statistics-education`, `data-science-education`, `statistical-modelling` | `https://aureliennicosiaulaval.github.io/MQT-2101/` |
| `arbres_quebec` | Quebec teaching dataset for data science and statistics education. | `open-data`, `quebec`, `teaching-datasets`, `data-science`, `statistics-education` | none |
| `vehicules-quebec` | Quebec vehicle dataset prepared for statistics and data science teaching. | `open-data`, `quebec`, `teaching-datasets`, `data-science`, `statistics-education` | none |
| `empress-of-ireland-data` | Teaching dataset on the RMS Empress of Ireland for reproducible data analysis. | `open-data`, `teaching-datasets`, `data-science`, `reproducible-research`, `statistics-education` | none |
| `grid-density-sparse-traversal` | Reproducible code and manuscript materials for sparse grid traversal in density estimation. | `r`, `density-estimation`, `nonparametric-statistics`, `computational-statistics`, `reproducible-research` | none |
| `evalue-HMM` | R package and research materials for predictive evaluation and diagnostics of hidden Markov models. | `r`, `r-package`, `hidden-markov-models`, `simulation`, `computational-statistics`, `reproducible-research` | `https://aureliennicosiaulaval.github.io/evalue-HMM/` |
| `UlavalSSD` | R package with datasets and utilities for statistics and data science teaching at Université Laval. | `r`, `r-package`, `teaching`, `statistics-education`, `data-science-education`, `teaching-datasets` | none |
| `Modele_etude_de_cas` | learnr template for reproducible interactive case studies. | `r`, `learnr`, `teaching`, `statistics-education`, `reproducible-research` | `https://aureliennicosiaulaval.github.io/site_ressources_SSD/` |
| `ulaval-template` | Quarto templates for statistics and data science teaching material at Université Laval. | `quarto`, `teaching`, `statistics-education`, `data-science-education`, `template` | none |
| `learnrTrackR` | R package prototype for tracking learnr tutorial attempts in teaching contexts. | `r`, `r-package`, `learnr`, `teaching`, `statistics-education`, `teaching-tools` | `https://aureliennicosiaulaval.github.io/learnrTrackR/` |
| `gmov` | R package for generative validation and diagnostics of SSF and iSSF movement models. | `r`, `r-package`, `movement-ecology`, `hidden-markov-models`, `step-selection-functions`, `simulation`, `reproducible-research` | `https://aureliennicosiaulaval.github.io/gmov/` |
| `contextR` | Emerging R package for contextual interpretation of statistical analyses. | `r`, `r-package`, `statistics`, `statistical-interpretation`, `computational-statistics`, `reproducible-research` | none |

## Repositories Requiring Manual Review

These repositories are public but sensitive, prototype-like, or tied to research materials that should not be presented as mature products. No automatic metadata update should be applied.

| Repository | Proposed cautious wording | Proposed topics | Proposed homepage | Reason for manual review |
|---|---|---|---|---|
| `HMMSSFGenerativeRepair` | Research package for generative validation of hidden Markov step-selection models. | `r`, `r-package`, `movement-ecology`, `hidden-markov-models`, `step-selection-functions`, `simulation`, `reproducible-research` | `https://aureliennicosiaulaval.github.io/HMMSSFGenerativeRepair/` | Sensitive research prototype. Confirm public positioning before applying metadata. |
| `gpt-cda-v2-prototype` | Prototype for course-aware teaching assistance and structured pedagogical workflows. | `ai-education`, `teaching-tools`, `statistical-interpretation` | none | Prototype. Validate what should be visible publicly before any update. |
| `corrective-hmm-states` | Pre-submission research materials on corrective hidden states in misspecified HMMs. | `hidden-markov-models`, `computational-statistics`, `simulation`, `reproducible-research` | none | Pre-submission materials. Do not make stronger public claims. |
| `geometry-aware-hsic-directional` | Reproducible research materials for geometry-aware HSIC tests with directional data. | `circular-statistics`, `directional-data`, `computational-statistics`, `reproducible-research` | none | Sensitive research materials. Current description is already careful. |
| `hsmm-finite-horizon-code-data` | Reproducible code and data for finite-horizon HSMM approximation error control. | `hidden-markov-models`, `computational-statistics`, `simulation`, `reproducible-research` | none | Sensitive research materials. Review manuscript status first. |

## Repositories To Not Touch For Now

These repositories should remain unchanged until their public role is clarified.

| Repository | Current issue | Candidate wording if later validated |
|---|---|---|
| `ZeroWasteData` | Streamlit prototype; current homepage did not complete a public automated HTTP check. | Streamlit prototype for automated data exploration and reproducible analysis suggestions. |
| `contextual-statistics-with-llm` | Sensitive LLM-related prototype and possible overlap with `contextR`. | Research prototype for contextual statistical interpretation with LLM-supported explanations. |

## Current Metadata Observations

All repositories in this plan were reachable through the GitHub API and reported as public on 2026-07-07. Every repository has a README according to the GitHub API. GitHub detected licenses for some repositories, but this plan does not modify any license file or license metadata.

GitHub Pages was detected and publicly checked for these repositories:

| Repository | Public URL | HTTP status |
|---|---|---|
| `DonutMap` | `https://aureliennicosiaulaval.github.io/DonutMap/` | 200 |
| `MQT-2101` | `https://aureliennicosiaulaval.github.io/MQT-2101/` | 200 |
| `HMMSSFGenerativeRepair` | `https://aureliennicosiaulaval.github.io/HMMSSFGenerativeRepair/` | 200 |
| `evalue-HMM` | `https://aureliennicosiaulaval.github.io/evalue-HMM/` | 200 |
| `learnrTrackR` | `https://aureliennicosiaulaval.github.io/learnrTrackR/` | 200 |
| `gmov` | `https://aureliennicosiaulaval.github.io/gmov/` | 200 |

The homepage `https://aureliennicosiaulaval.github.io/site_ressources_SSD/`, currently used by `Modele_etude_de_cas`, also responded with HTTP 200.

No homepage is proposed for repositories where no existing public homepage responded successfully.

## Risks

- A short GitHub description can make a prototype look more mature than intended. Sensitive repositories are therefore marked `review_manually` or `do_not_touch`.
- Adding topics to pre-submission research materials can increase discoverability before the manuscript or public framing is ready.
- A homepage should not be added just because a predictable GitHub Pages URL exists. Only URLs that responded publicly are proposed.
- Repository metadata is not versioned. The YAML file is a reviewable plan, not a source of truth unless Aurélien later decides to use it operationally.

## Validation Checklist

Before applying any metadata update outside this repository:

- confirm that the repository name is unchanged;
- confirm that the repository visibility is unchanged;
- confirm that no repository is archived;
- confirm that no license is modified;
- confirm that no DOI is modified;
- confirm that no GitHub Pages URL is changed;
- confirm that proposed topics are at most 20 per repository;
- confirm that every proposed homepage responds publicly;
- confirm that no sensitive repository has action `update_metadata`;
- confirm that non-public repositories do not appear in public recommendations;
- confirm that prototype wording remains explicit when applicable.

## Scope Of This Pull Request

This pull request only adds a reviewable metadata plan to `AurelienNicosiaULaval/web_site`. It does not update GitHub descriptions, topics, homepages, visibility, repository names, DOI records, licenses, GitHub Pages configuration, code, package files or research content.
