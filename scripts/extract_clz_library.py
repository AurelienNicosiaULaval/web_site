#!/usr/bin/env python3
"""Extract a compact library catalogue from a CLZ Books PDF export.

Run reproducibly with:

    uv run --with pdfplumber python scripts/extract_clz_library.py \
      /path/to/clz-export.pdf assets/library/library-data.json

The PDF is a ruled table. Some records are split at a page boundary, so the
script detects and joins those fragments before writing the JSON catalogue.
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

import pdfplumber


FIELDS = (
    "author",
    "title",
    "isbn",
    "publisher",
    "publication_date",
    "genre",
    "publication_year",
    "series",
)

TRAILING_CONNECTORS = re.compile(
    r"\b(a|an|and|applied|de|des|du|et|for|in|la|le|les|of|or|the|to|un|une)$",
    flags=re.IGNORECASE,
)


def clean_cell(value: str | None) -> str:
    """Collapse PDF line breaks and normalize Unicode without changing text."""
    return unicodedata.normalize("NFC", " ".join((value or "").split()))


def row_to_record(row: list[str | None], page_number: int) -> dict[str, object]:
    values = [clean_cell(value) for value in row[: len(FIELDS)]]
    values.extend([""] * (len(FIELDS) - len(values)))
    record: dict[str, object] = dict(zip(FIELDS, values, strict=True))
    record["source_pages"] = [page_number]
    return record


def is_header(record: dict[str, object]) -> bool:
    return record["author"] == "Author" and record["title"] == "Title"


def is_blank(record: dict[str, object]) -> bool:
    return not any(record[field] for field in FIELDS)


def has_year(value: object) -> bool:
    return bool(re.search(r"\b(?:18|19|20)\d{2}\b", str(value)))


def is_page_continuation(
    current: dict[str, object], previous: dict[str, object]
) -> bool:
    """Identify a record fragment appearing as the first row of a new page."""
    if current["isbn"] or current["publication_year"]:
        return False

    previous_title = str(previous["title"]).rstrip(" ,;:-")
    previous_author = str(previous["author"]).rstrip()
    previous_date = str(previous["publication_date"])

    return any(
        (
            not current["author"],
            not current["title"],
            str(current["author"]).lstrip().startswith("|"),
            previous_author.endswith("|"),
            not has_year(previous_date),
            bool(TRAILING_CONNECTORS.search(previous_title)),
            str(previous["title"]).count("(") > str(previous["title"]).count(")"),
        )
    )


def merge_fragment(target: dict[str, object], fragment: dict[str, object]) -> None:
    for field in FIELDS:
        addition = str(fragment[field]).strip()
        if not addition:
            continue
        existing = str(target[field]).strip()
        target[field] = f"{existing} {addition}".strip()

    pages = list(target["source_pages"])
    pages.extend(fragment["source_pages"])
    target["source_pages"] = sorted(set(pages))


def extract_catalogue(pdf_path: Path) -> tuple[list[dict[str, object]], int]:
    records: list[dict[str, object]] = []

    with pdfplumber.open(pdf_path) as pdf:
        page_count = len(pdf.pages)

        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            if len(tables) != 1:
                raise RuntimeError(
                    f"Expected one table on page {page_number}, found {len(tables)}."
                )

            for row_number, row in enumerate(tables[0]):
                record = row_to_record(row, page_number)

                if is_header(record) or is_blank(record):
                    continue

                if row_number == 0 and records and is_page_continuation(record, records[-1]):
                    merge_fragment(records[-1], record)
                    continue

                records.append(record)

    for index, record in enumerate(records, start=1):
        record["id"] = f"book-{index:04d}"

    return records, page_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_pdf", type=Path)
    parser.add_argument("output_json", type=Path)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records, page_count = extract_catalogue(args.input_pdf)
    payload = {
        "source": {
            "name": args.input_pdf.name,
            "format": "CLZ Books PDF export",
            "pages": page_count,
        },
        "records": records,
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Extracted {len(records)} records from {page_count} pages.")


if __name__ == "__main__":
    main()
