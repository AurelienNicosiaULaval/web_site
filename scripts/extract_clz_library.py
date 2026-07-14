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
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

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


def normalized_key(value: object) -> str:
    """Normalize spacing and punctuation for stable record reconciliation."""
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    without_marks = "".join(
        character
        for character in normalized
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", " ", without_marks.casefold()).strip()


def record_signature(record: dict[str, Any], normalized: bool = False) -> tuple[str, ...]:
    values = tuple(str(record.get(field, "")) for field in FIELDS)
    if normalized:
        return tuple(normalized_key(value) for value in values)
    return values


def normalized_isbn(record: dict[str, Any]) -> str:
    return re.sub(r"[^0-9Xx]", "", str(record.get("isbn", ""))).upper()


def numeric_id(record_id: object) -> int | None:
    match = re.fullmatch(r"book-(\d+)", str(record_id))
    return int(match.group(1)) if match else None


def preserve_record_ids(
    records: list[dict[str, object]],
    previous_records: list[dict[str, Any]],
) -> dict[str, int]:
    """Keep identifiers stable when a new CLZ export reorders the catalogue.

    Exact rows are matched first. Remaining rows use ISBN, then a normalized
    bibliographic signature so harmless PDF line-wrap changes do not detach
    manual curation or non-ISBN cover matches from their records.
    """
    unmatched_previous = set(range(len(previous_records)))
    assigned_previous: dict[int, int] = {}

    def assign(new_index: int, previous_index: int) -> None:
        records[new_index]["id"] = previous_records[previous_index]["id"]
        assigned_previous[new_index] = previous_index
        unmatched_previous.remove(previous_index)

    exact_lookup: dict[tuple[str, ...], deque[int]] = defaultdict(deque)
    for previous_index, previous in enumerate(previous_records):
        exact_lookup[record_signature(previous)].append(previous_index)
    for new_index, record in enumerate(records):
        candidates = exact_lookup.get(record_signature(record))
        while candidates and candidates[0] not in unmatched_previous:
            candidates.popleft()
        if candidates:
            assign(new_index, candidates.popleft())

    isbn_lookup: dict[str, list[int]] = defaultdict(list)
    for previous_index in unmatched_previous:
        isbn = normalized_isbn(previous_records[previous_index])
        if isbn:
            isbn_lookup[isbn].append(previous_index)
    for new_index, record in enumerate(records):
        if new_index in assigned_previous:
            continue
        isbn = normalized_isbn(record)
        candidates = [
            previous_index
            for previous_index in isbn_lookup.get(isbn, [])
            if previous_index in unmatched_previous
        ]
        if not candidates:
            continue
        normalized_record = record_signature(record, normalized=True)

        def candidate_score(previous_index: int) -> tuple[int, int]:
            previous = previous_records[previous_index]
            normalized_previous = record_signature(previous, normalized=True)
            agreements = sum(
                bool(current) and current == earlier
                for current, earlier in zip(
                    normalized_record,
                    normalized_previous,
                )
            )
            completeness = sum(bool(value) for value in normalized_previous)
            return agreements, completeness

        assign(new_index, max(candidates, key=candidate_score))

    normalized_lookup: dict[tuple[str, ...], deque[int]] = defaultdict(deque)
    for previous_index in unmatched_previous:
        normalized_lookup[
            record_signature(previous_records[previous_index], normalized=True)
        ].append(previous_index)
    for new_index, record in enumerate(records):
        if new_index in assigned_previous:
            continue
        candidates = normalized_lookup.get(record_signature(record, normalized=True))
        while candidates and candidates[0] not in unmatched_previous:
            candidates.popleft()
        if candidates:
            assign(new_index, candidates.popleft())

    existing_numbers = [
        number
        for previous in previous_records
        if (number := numeric_id(previous.get("id"))) is not None
    ]
    next_number = max(existing_numbers, default=0) + 1
    new_record_count = 0
    for new_index, record in enumerate(records):
        if new_index in assigned_previous:
            continue
        record["id"] = f"book-{next_number:04d}"
        next_number += 1
        new_record_count += 1

    record_ids = [str(record["id"]) for record in records]
    if len(record_ids) != len(set(record_ids)):
        raise RuntimeError("Stable record reconciliation produced duplicate IDs.")

    return {
        "retained": len(assigned_previous),
        "added": new_record_count,
        "removed": len(previous_records) - len(assigned_previous),
    }


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
    parser.add_argument(
        "--previous",
        type=Path,
        help="Previous raw catalogue used to preserve stable record IDs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records, page_count = extract_catalogue(args.input_pdf)
    reconciliation = None
    previous_catalogue = None
    if args.previous:
        previous_payload = json.loads(args.previous.read_text(encoding="utf-8"))
        reconciliation = preserve_record_ids(records, previous_payload["records"])
        previous_catalogue = previous_payload.get("source", {}).get(
            "name", str(args.previous)
        )
    payload = {
        "source": {
            "name": args.input_pdf.name,
            "format": "CLZ Books PDF export",
            "pages": page_count,
        },
        "records": records,
    }
    if reconciliation is not None:
        payload["source"]["previous_catalogue"] = previous_catalogue
        payload["source"]["reconciliation"] = reconciliation

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    message = f"Extracted {len(records)} records from {page_count} pages."
    if reconciliation is not None:
        message += (
            f" Retained {reconciliation['retained']} stable IDs; "
            f"added {reconciliation['added']}; removed {reconciliation['removed']}."
        )
    print(message)


if __name__ == "__main__":
    main()
