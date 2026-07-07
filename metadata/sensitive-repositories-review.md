# Sensitive Repositories Review

Date: 2026-07-07

Scope: decision document only. This review does not modify any repository, README, code, license, DOI, GitHub Pages URL, repository name, visibility setting, topic, homepage or archive status.

## Summary

This document identifies repositories that are public but sensitive, prototype-like, or tied to work in preparation. Its purpose is to support a human decision before any future public positioning work.

The review is based on GitHub repository metadata checked on 2026-07-07 and on the existing metadata plan in `metadata/github-repositories.yml`. It is not a full scientific review of repository contents. No sensitive repository was cloned or modified while preparing this document.

Allowed recommendation categories:

- `keep_private_or_unlisted`
- `keep_public_but_discreet`
- `clarify_as_prototype`
- `clarify_as_reproducible_materials`
- `safe_to_feature_later`
- `needs_human_decision`

No automatic archiving, deletion, license change, DOI change or visibility change is recommended.

## Main Review Table

| Repository | Apparent public status | Current description | Current topics | Current homepage | Estimated maturity | Sensitivity | Public visibility risk | Scientific risk | Pedagogical risk | Institutional risk | Provisional recommendation |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `HMMSSFGenerativeRepair` | Public | Empty | none | GitHub homepage metadata: none. Existing Pages URL detected: `https://aureliennicosiaulaval.github.io/HMMSSFGenerativeRepair/` | Research prototype | High | Moderate | High | Low | Moderate | `keep_public_but_discreet` |
| `gpt-cda-v2-prototype` | Public | Empty | none | none | Prototype | High | High | Moderate | High | High | `clarify_as_prototype` |
| `ZeroWasteData` | Public | Streamlit prototype for automated data exploration and analysis suggestions; generates Python and R code and exportable HTML reports. | none | `https://zerowastedata.streamlit.app` | Application prototype | High | Moderate | Moderate | Moderate | Moderate | `clarify_as_prototype` |
| `contextual-statistics-with-llm` | Public | Package R contextR enrichissant les analyses statistiques (lm, ANOVA, PCA, etc.) avec des interprétations contextuelles générées par LLM. | none | none | LLM-related research prototype | High | High | Moderate | High | High | `needs_human_decision` |
| `corrective-hmm-states` | Public | Corrective hidden states in misspecified HMMs | none | none | Pre-submission research materials | High | Moderate | High | Low | Moderate | `keep_public_but_discreet` |
| `geometry-aware-hsic-directional` | Public | Replication materials for geometry-aware HSIC independence testing for circular, toroidal and circular-linear data | none | none | Reproducible research materials | Moderate | Low to moderate | Moderate | Low | Low | `clarify_as_reproducible_materials` |
| `hsmm-finite-horizon-code-data` | Public | Code and data package for finite-horizon HSMM approximation error control | none | none | Reproducible code and data | Moderate to high | Moderate | High | Low | Moderate | `clarify_as_reproducible_materials` |
| `GLBFP_OS` | Private in authenticated GitHub check; not publicly accessible | Not reproduced in this public decision document. | Not reproduced in this public decision document. | Not reproduced in this public decision document. | Manuscript and research materials | Very high | High if surfaced publicly | High | Low | High | `keep_private_or_unlisted` |

## Repository Notes

### `HMMSSFGenerativeRepair`

Current public signal:

- Public repository.
- No short GitHub description is currently set.
- No topics are currently set.
- No GitHub homepage metadata is currently set.
- A GitHub Pages URL was detected and returned HTTP 200: `https://aureliennicosiaulaval.github.io/HMMSSFGenerativeRepair/`.

Assessment:

This appears to be a research prototype related to generative validation of hidden Markov step-selection models. It should not be presented as a mature package unless Aurélien explicitly confirms its status, documentation level and relation to submitted or planned manuscripts.

Provisional recommendation:

`keep_public_but_discreet`

Justification:

The repository can remain available for collaborators or reproducibility, but it should not be featured as a flagship project until its scientific positioning, manuscript status and public documentation are confirmed.

Future action, only after validation:

- Clarify whether the repository is a package, a research prototype, or reproducible research material.
- If public positioning is approved, use cautious wording such as "research prototype" or "research materials".
- Do not add stronger metadata, badges or public navigation links before human review.

### `gpt-cda-v2-prototype`

Current public signal:

- Public repository.
- No short GitHub description is currently set.
- No topics are currently set.
- No homepage is currently set.

Assessment:

This repository should remain treated as a sensitive prototype. Its name suggests an implementation or second-generation prototype related to course-aware teaching assistance. That creates public interpretation risks around maturity, institutional endorsement, privacy, student use and pedagogical validation.

Provisional recommendation:

`clarify_as_prototype`

Justification:

If the repository remains public, its public surface should explicitly signal prototype status and avoid claims about validated educational effectiveness unless supported by evidence. It should not be featured as a mature teaching platform.

Future action, only after validation:

- Decide whether the repository should remain publicly discoverable.
- If public, add a cautious prototype notice.
- Confirm that no private student data, credentials, deployment details or institutional internal workflows are exposed.
- Keep it separate from the main Research Lab feature list unless Aurélien approves a public framing.

### `ZeroWasteData`

Current public signal:

- Public repository.
- Current description: "Streamlit prototype for automated data exploration and analysis suggestions; generates Python and R code and exportable HTML reports."
- No topics are currently set.
- Current homepage: `https://zerowastedata.streamlit.app`.
- Automated homepage validation was inconclusive because the Streamlit URL redirected during `curl` verification.

Assessment:

This should remain treated as an application prototype. The current description is already explicit about prototype status, which is useful. The main risk is that visitors may interpret the app as a polished, validated service if linked too prominently.

Provisional recommendation:

`clarify_as_prototype`

Justification:

The repository can be useful as an innovation or exploratory data-science prototype, but it should not be mixed with core research software or mature teaching resources.

Future action, only after validation:

- Confirm whether the Streamlit app is still intended to be public.
- Add or keep prototype wording in public descriptions.
- Avoid featuring it as a production tool.
- If later linked from the website, place it under innovation or prototypes rather than core research packages.

### `contextual-statistics-with-llm`

Current public signal:

- Public repository.
- Current description: "Package R contextR enrichissant les analyses statistiques (lm, ANOVA, PCA, etc.) avec des interprétations contextuelles générées par LLM."
- No topics are currently set.
- No homepage is currently set.

Assessment:

This repository should not be featured until its role relative to `contextR` is clarified. The current name and description create overlap with the public `contextR` project, while also introducing stronger LLM-related claims than the current public ecosystem needs.

Provisional recommendation:

`needs_human_decision`

Justification:

This repository could confuse visitors if it appears beside `contextR` without a clear distinction between prototype, experiment, teaching demonstration and package roadmap. It may also imply a mature AI-assisted interpretation workflow before the public positioning is settled.

Future action, only after validation:

- Decide whether this repository is historical, experimental, teaching-related, or a precursor to `contextR`.
- Decide whether it should remain visible in public navigation.
- If it remains public, add a clear prototype or experimental notice.
- Do not link it from the Research Lab, profile README or `contextR` README until Aurélien approves the relationship.

### `corrective-hmm-states`

Current public signal:

- Public repository.
- Current description: "Corrective hidden states in misspecified HMMs".
- No topics are currently set.
- No homepage is currently set.

Assessment:

This appears to be research material tied to a methodological idea or manuscript-stage project. The current description is concise, but it does not state whether the repository is exploratory, pre-submission, supplementary material, or a completed reproducibility package.

Provisional recommendation:

`keep_public_but_discreet`

Justification:

The repository can remain public if that is intentional, but it should not be highlighted as a finished research output until manuscript status and public claims are confirmed.

Future action, only after validation:

- Confirm whether the associated work is submitted, in preparation, under review, accepted or exploratory.
- If appropriate, add cautious wording such as "pre-submission research materials".
- Avoid adding broad topics that increase discoverability before the manuscript status is clear.

### `geometry-aware-hsic-directional`

Current public signal:

- Public repository.
- Current description: "Replication materials for geometry-aware HSIC independence testing for circular, toroidal and circular-linear data".
- No topics are currently set.
- No homepage is currently set.

Assessment:

This repository already uses relatively cautious wording by presenting itself as replication material. It appears closer to reproducible research material than to a software package.

Provisional recommendation:

`clarify_as_reproducible_materials`

Justification:

The repository may be appropriate for public visibility if the associated paper or preprint is ready to be linked. It should not be described as a general-purpose package unless the repository structure and documentation support that framing.

Future action, only after validation:

- Confirm the associated manuscript or preprint status.
- If public positioning is approved, keep wording focused on "replication materials" or "reproducible research materials".
- Add links to publication, preprint or citation only when those links are stable and approved.

### `hsmm-finite-horizon-code-data`

Current public signal:

- Public repository.
- Current description: "Code and data package for finite-horizon HSMM approximation error control".
- No topics are currently set.
- No homepage is currently set.

Assessment:

This appears to be code and data linked to finite-horizon HSMM approximation research. Because it may be tied to a manuscript, its public framing should remain careful until publication, preprint and citation status are settled.

Provisional recommendation:

`clarify_as_reproducible_materials`

Justification:

The repository can be framed as reproducible code and data, but not as a mature package. The term "package" in the current description could be interpreted as software-package maturity unless clarified.

Future action, only after validation:

- Confirm whether this is a replication package, supplementary material, or ongoing research code.
- If public positioning is approved, clarify that it is reproducible code and data.
- Do not add public badges, citation text or website navigation before the manuscript status is confirmed.

### `GLBFP_OS`

Current public signal:

- Private in authenticated GitHub check.
- Not publicly accessible.
- Current private description, topics and homepage are not reproduced in this public decision document.

Assessment:

This repository should remain outside the public ecosystem surface unless Aurélien makes a separate explicit decision. Because it appears to contain manuscript or research materials, its public role should be reviewed independently from the public `GLBFP` package and related reproducible materials.

Provisional recommendation:

`keep_private_or_unlisted`

Justification:

The repository is not public and should not be surfaced through the public website, profile README, Research Lab page or cross-repository README boxes by default.

Future action, only after validation:

- Decide whether any part of its contents should ever become public.
- If public release is needed, prepare a separate release plan with rights, manuscript, DOI, citation and reproducibility checks.
- Do not expose private metadata or internal manuscript structure in public-facing documentation.

## Decisions For Aurélien

Before any future PR or metadata action, Aurélien should decide:

- Which repositories, if any, should remain public but intentionally discreet?
- Which repositories need a prototype notice in their README?
- Which repositories are linked to submitted, accepted or in-preparation manuscripts?
- Which repositories should be treated as reproducible research materials rather than packages?
- Should `HMMSSFGenerativeRepair` be visible as a research prototype, or should it remain unfeatured until manuscript status is clearer?
- Should `gpt-cda-v2-prototype` remain public, and what institutional or privacy review is needed before public positioning?
- Should `ZeroWasteData` remain linked from the website while it is a prototype application?
- What is the intended relationship between `contextual-statistics-with-llm` and `contextR`?
- Should `corrective-hmm-states` remain discoverable before publication or submission?
- Are `geometry-aware-hsic-directional` and `hsmm-finite-horizon-code-data` ready to be described as public reproducible research materials?
- Should `GLBFP_OS` remain private or unlisted in all public ecosystem documents?

## Checklist Before Any Future Action

Before changing any sensitive repository, verify:

- Aurélien has approved the specific repository and action.
- The action does not rename any repository.
- The action does not change repository visibility.
- The action does not archive any repository.
- The action does not delete any repository or file.
- The action does not modify any license or license metadata.
- The action does not modify any DOI or citation target.
- The action does not change any existing GitHub Pages URL.
- The action does not modify code.
- The action does not expose private repository metadata.
- The action does not present a prototype as a mature package or validated educational tool.
- The action does not link `contextual-statistics-with-llm` from `contextR` or the public ecosystem before the relationship is approved.
- The action keeps manuscript-stage or pre-submission repositories discreet unless public release is explicitly approved.
- Any wording added to a repository is cautious, factual and reversible.

## Recommended Next Step

No repository action should follow automatically from this document. The next step is a human decision by Aurélien on each repository category, followed by small independent PRs only for the repositories and wording he approves.
