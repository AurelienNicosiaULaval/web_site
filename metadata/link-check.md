# Public Link Check

This repository includes a lightweight link checker for the public GitHub ecosystem around Aurélien Nicosia's research, teaching resources and scientific software.

The tool is intentionally non-destructive. It only reads URLs listed in `metadata/link-check.yml`, reports their status and exits with an error only when a required public link fails.

## Why This Exists

The GitHub ecosystem now links together the profile README, the personal website, the Research Lab page, public GitHub Pages sites, pkgdown sites, DOI records, public repositories and teaching resources.

This check helps detect broken public links before future documentation or website updates are merged. It does not change any URL, DOI, repository metadata, GitHub Pages setting, license, visibility or file outside this repository.

## Files

- `metadata/link-check.yml`: list of public URLs to check, grouped by category.
- `scripts/check-links.py`: dependency-light Python script that checks the configured URLs.
- `.github/workflows/check-links.yml`: manual GitHub Actions workflow.

## Categories

The configuration uses these categories:

- `core_site`: main website and Research Lab page.
- `github_pages`: public GitHub Pages or pkgdown sites.
- `repositories`: public GitHub repositories.
- `doi`: public DOI resolver links.
- `profiles`: public profile links such as ORCID or GitHub.
- `teaching`: public teaching and pedagogical resource sites.
- `optional_external`: external applications or profiles where automated checks may be blocked or rate-limited.

## Run Locally

From the root of `web_site`:

```bash
python3 scripts/check-links.py metadata/link-check.yml
```

The script prints one tab-separated line per URL:

- `result`: `ok`, `warning` or `failed`;
- `status`: HTTP status code, or `ERROR` when no HTTP response was obtained;
- `category`: category from the YAML configuration;
- `name`: human-readable label;
- `url`: checked URL.

The final summary reports the number of checked links, warnings and failures.

## Interpret Results

`ok` means the URL responded with an HTTP status in the 200 to 399 range.

`warning` means the URL did not return a normal success status, but the link is marked as optional or known to be unreliable for automated checks. This can happen with:

- LinkedIn or other profile pages that block automated requests;
- Streamlit or similar external applications that sleep, redirect, rate-limit or return temporary service responses.

`failed` means a required public URL did not respond successfully. These failures should be reviewed manually. The script never edits or fixes links automatically.

## What Not To Add

Do not add:

- private repositories;
- non-public repositories;
- sensitive prototypes that should not be discoverable;
- manuscript repositories that are not intended for public navigation;
- URLs containing private tokens, signed links or temporary access keys;
- unpublished DOI targets;
- speculative GitHub Pages URLs that have not been validated publicly.

If a repository is sensitive or still under human review, keep it out of `metadata/link-check.yml` until Aurélien explicitly approves its public role.

## Manual Workflow

The GitHub Actions workflow is manual only. It is triggered with `workflow_dispatch` and does not run on push or pull request events.

The workflow runs the same command:

```bash
python3 scripts/check-links.py metadata/link-check.yml
```

## Maintenance Notes

When adding a new public link:

1. Confirm the repository or page is public.
2. Confirm the URL is stable and intended for public use.
3. Add it to the appropriate category in `metadata/link-check.yml`.
4. Run the local script.
5. Review any warnings before merging.

Do not use this tool to change URLs. It is only a monitoring aid for public documentation links.
