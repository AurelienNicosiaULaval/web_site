#!/usr/bin/env python3
"""Curate the extracted CLZ catalogue without destroying its raw evidence.

The pipeline reads the immutable PDF extraction, fills only empty fields from
exact-ISBN Open Library records, applies manually sourced high-confidence
overrides, normalizes publisher labels for analysis, and emits both the public
catalogue and a machine-readable quality report.

Run from the project root:

    python3 scripts/curate_library_data.py
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / "data/library/clz-library-raw.json"
DEFAULT_CACHE = ROOT / "data/library/openlibrary-isbn-cache.json"
DEFAULT_DIRECT_COVER_CACHE = ROOT / "data/library/openlibrary-direct-cover-cache.json"
DEFAULT_OPENLIBRARY_COVER_SEARCH = ROOT / "data/library/openlibrary-cover-search-cache.json"
DEFAULT_GOOGLE_COVER_CACHE = ROOT / "data/library/google-books-cover-cache.json"
DEFAULT_ELLIPSES_COVER_CACHE = ROOT / "data/library/ellipses-cover-cache.json"
DEFAULT_CURATION = ROOT / "data/library/library-curation.json"
DEFAULT_OUTPUT = ROOT / "assets/library/library-data.json"
DEFAULT_REPORT = ROOT / "data/library/library-quality-report.json"

PUBLISHER_ALIASES = {
    "belin": "Belin",
    "calvage et mounet": "Calvage & Mounet",
    "calvage mounet": "Calvage & Mounet",
    "cassini": "Cassini",
    "de boeck sup": "De Boeck Supérieur",
    "dunod": "Dunod",
    "editions mir": "Éditions Mir",
    "edp sciences": "EDP Sciences",
    "ellipses": "Ellipses",
    "erpi": "ERPI",
    "flammarion": "Flammarion",
    "j ai lu": "J'ai lu",
    "les presses de l universite laval": "Presses de l’Université Laval",
    "modulo": "Modulo",
    "pearson": "Pearson",
    "presses de l universite laval": "Presses de l’Université Laval",
    "presses universitaires de france": "Presses Universitaires de France",
    "presses universitaires de france puf": "Presses Universitaires de France",
    "puf": "Presses Universitaires de France",
    "que sais je": "Que sais-je?",
    "rba": "RBA",
    "rba france": "RBA",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_marks = "".join(character for character in normalized if not unicodedata.combining(character))
    return re.sub(r"[^a-z0-9]+", " ", without_marks.casefold()).strip()


def normalize_isbn(value: str) -> str:
    return re.sub(r"[^0-9Xx]", "", value).upper()


def valid_isbn10(value: str) -> bool:
    if not re.fullmatch(r"\d{9}[\dX]", value):
        return False
    total = sum((10 - index) * (10 if character == "X" else int(character)) for index, character in enumerate(value))
    return total % 11 == 0


def valid_isbn13(value: str) -> bool:
    if not re.fullmatch(r"\d{13}", value):
        return False
    total = sum(int(character) * (1 if index % 2 == 0 else 3) for index, character in enumerate(value[:12]))
    return (10 - total % 10) % 10 == int(value[-1])


def valid_isbn(value: str) -> bool:
    return valid_isbn10(value) or valid_isbn13(value)


def parse_year(value: str) -> int | None:
    match = re.search(r"\b(18|19|20)\d{2}\b", value or "")
    return int(match.group(0)) if match else None


def publisher_normalized(value: str) -> str:
    if not value:
        return ""
    key = normalize_text(value)
    return PUBLISHER_ALIASES.get(key, re.sub(r"\s+", " ", value).strip())


def authors_from_openlibrary(entry: dict[str, Any]) -> str:
    names = [author.get("name", "").strip() for author in entry.get("authors", [])]
    return " | ".join(name for name in names if name)


def publisher_from_openlibrary(entry: dict[str, Any]) -> str:
    publishers = entry.get("publishers", [])
    if not publishers:
        return ""
    return str(publishers[0].get("name", "")).strip()


def title_from_openlibrary(entry: dict[str, Any]) -> str:
    title = str(entry.get("title", "")).strip()
    subtitle = str(entry.get("subtitle", "")).strip()
    return f"{title}: {subtitle}" if title and subtitle else title


def openlibrary_summary(entry: dict[str, Any], retrieved_on: str) -> dict[str, Any]:
    subjects = [
        str(subject.get("name", "")).strip()
        for subject in entry.get("subjects", [])
        if str(subject.get("name", "")).strip()
    ]
    cover = entry.get("cover", {})
    return {
        "provider": "Open Library",
        "retrieved_on": retrieved_on,
        "key": entry.get("key", ""),
        "url": str(entry.get("url", "")).replace("http://", "https://"),
        "title": entry.get("title", ""),
        "authors": [author.get("name", "") for author in entry.get("authors", [])],
        "publishers": [publisher.get("name", "") for publisher in entry.get("publishers", [])],
        "publish_date": entry.get("publish_date", ""),
        "subjects": subjects[:12],
        "cover": {
            size: str(cover.get(size, "")).replace("http://", "https://")
            for size in ("small", "medium", "large")
            if cover.get(size)
        },
    }


def cover_summary(
    provider: str,
    source_id: str,
    retrieved_on: str,
    match_method: str,
    source_url: str,
    images: dict[str, str],
    confidence: str = "high",
) -> dict[str, Any]:
    return {
        "provider": provider,
        "source_id": source_id,
        "retrieved_on": retrieved_on,
        "match_method": match_method,
        "confidence": confidence,
        "source_url": str(source_url).replace("http://", "https://"),
        "images": {
            size: str(url).replace("http://", "https://")
            for size, url in images.items()
            if url
        },
    }


def google_cover_images(thumbnail_url: str) -> dict[str, str]:
    thumbnail = str(thumbnail_url).replace("http://", "https://")
    if not thumbnail:
        return {}
    return {
        "small": thumbnail,
        "medium": re.sub(r"([?&])zoom=5(?=&|$)", r"\1zoom=2", thumbnail),
        "large": re.sub(r"([?&])zoom=5(?=&|$)", r"\1zoom=3", thumbnail),
    }


def fill_from_openlibrary(
    record: dict[str, Any],
    entry: dict[str, Any],
    provenance: dict[str, str],
) -> list[str]:
    candidates = {
        "title": title_from_openlibrary(entry),
        "author": authors_from_openlibrary(entry),
        "publisher": publisher_from_openlibrary(entry),
        "publication_date": str(entry.get("publish_date", "")).strip(),
    }
    filled: list[str] = []
    for field, value in candidates.items():
        if not record.get(field) and value:
            record[field] = value
            provenance[field] = "openlibrary_exact"
            filled.append(field)

    if not record.get("publication_year"):
        year = parse_year(candidates["publication_date"])
        if year is not None:
            record["publication_year"] = str(year)
            provenance["publication_year"] = "openlibrary_exact"
            filled.append("publication_year")
    return filled


def apply_overrides(
    records: list[dict[str, Any]],
    curation: dict[str, Any],
) -> list[dict[str, Any]]:
    by_id = {record["id"]: record for record in records}
    applied: list[dict[str, Any]] = []
    for override in curation["overrides"]:
        record = by_id.get(override["id"])
        if record is None:
            raise RuntimeError(f"Unknown record in curation file: {override['id']}")
        if override.get("confidence") != "high":
            raise RuntimeError(f"Non-high-confidence override refused: {override['id']}")

        before = {field: record.get(field, "") for field in override["changes"]}
        effective_changes = {
            field: value
            for field, value in override["changes"].items()
            if before[field] != value
        }
        record.update(override["changes"])
        provenance = record.setdefault("data_provenance", {})
        source_label = ",".join(override["sources"])
        for field in override["changes"]:
            provenance[field] = source_label
        record["curation"] = {
            "confidence": override["confidence"],
            "reason": override["reason"],
            "sources": override["sources"],
            "changed_fields": list(effective_changes),
            "verified_fields": list(override["changes"]),
        }
        applied.append({
            "id": override["id"],
            "before": before,
            "after": effective_changes,
            "sources": override["sources"],
        })
    return applied


def classify_records(records: list[dict[str, Any]]) -> None:
    isbn_groups: dict[str, list[str]] = defaultdict(list)
    title_author_groups: dict[tuple[str, str], list[str]] = defaultdict(list)

    for record in records:
        isbn = normalize_isbn(str(record.get("isbn", "")))
        if isbn and valid_isbn(isbn):
            isbn_groups[isbn].append(record["id"])
        title_author_key = (
            normalize_text(str(record.get("title", ""))),
            normalize_text(str(record.get("author", ""))),
        )
        if all(title_author_key):
            title_author_groups[title_author_key].append(record["id"])

    for record in records:
        flags: list[str] = []
        raw_isbn = str(record.get("isbn", ""))
        isbn = normalize_isbn(raw_isbn)
        year = parse_year(str(record.get("publication_year", "")))

        if isbn and valid_isbn(isbn):
            record["isbn"] = isbn
            record["isbn_status"] = "valid"
        elif isbn:
            record["isbn_status"] = "invalid"
            flags.append("invalid_isbn")
        elif year is None:
            record["isbn_status"] = "missing_unknown_year"
            flags.append("missing_isbn_unknown_year")
        elif year < 1970:
            record["isbn_status"] = "missing_pre_1970"
        else:
            record["isbn_status"] = "missing_1970_or_later"
            flags.append("missing_isbn_1970_or_later")

        if not record.get("title"):
            flags.append("missing_title")
        if not record.get("author"):
            flags.append("missing_author")
        if not record.get("publisher"):
            flags.append("missing_publisher")
        if year is None:
            flags.append("missing_or_invalid_year")

        record["publisher_normalized"] = publisher_normalized(str(record.get("publisher", "")))
        valid_record_isbn = record["isbn"] if record["isbn_status"] == "valid" else ""
        if valid_record_isbn and len(isbn_groups[valid_record_isbn]) > 1:
            flags.append("shared_isbn_possible_multiple_copy")

        title_author_key = (
            normalize_text(str(record.get("title", ""))),
            normalize_text(str(record.get("author", ""))),
        )
        if all(title_author_key) and len(title_author_groups[title_author_key]) > 1:
            flags.append("same_title_author_possible_multiple_copy")
        record["quality_flags"] = flags


def build_quality_report(
    raw_records: list[dict[str, Any]],
    records: list[dict[str, Any]],
    applied: list[dict[str, Any]],
    openlibrary_matches: int,
    openlibrary_fills: Counter[str],
    curated_on: str,
) -> dict[str, Any]:
    isbn_status = Counter(record["isbn_status"] for record in records)
    valid_isbns = {
        record["isbn"]
        for record in records
        if record["isbn_status"] == "valid"
    }
    matched_isbns = {
        record["isbn"]
        for record in records
        if record["isbn_status"] == "valid" and record.get("openlibrary")
    }
    quality_flags = Counter(flag for record in records for flag in record["quality_flags"])
    publisher_values = {
        record["publisher_normalized"]
        for record in records
        if record["publisher_normalized"]
    }
    missing_fields = {
        field: sum(not bool(record.get(field)) for record in records)
        for field in ("author", "title", "isbn", "publisher", "publication_date", "publication_year", "genre", "series")
    }
    raw_missing_fields = {
        field: sum(not bool(record.get(field)) for record in raw_records)
        for field in ("author", "title", "isbn", "publisher", "publication_date", "publication_year", "genre", "series")
    }
    raw_publisher_labels = {
        str(record.get("publisher", "")).strip()
        for record in raw_records
        if str(record.get("publisher", "")).strip()
    }
    cover_providers = Counter(
        record.get("cover", {}).get("provider", "")
        for record in records
        if record.get("cover", {}).get("images", {}).get("medium")
    )
    cover_match_methods = Counter(
        record.get("cover", {}).get("match_method", "")
        for record in records
        if record.get("cover", {}).get("images", {}).get("medium")
    )
    cover_record_count = sum(cover_providers.values())
    return {
        "generated_on": curated_on,
        "record_count": len(records),
        "raw_record_count": len(raw_records),
        "manual_override_count": len(applied),
        "manual_field_change_count": sum(len(item["after"]) for item in applied),
        "openlibrary_exact_match_count": openlibrary_matches,
        "openlibrary_exact_match_rate": round(openlibrary_matches / len(records), 4),
        "unique_valid_isbn_count": len(valid_isbns),
        "openlibrary_unique_isbn_match_count": len(matched_isbns),
        "openlibrary_unique_isbn_match_rate": round(len(matched_isbns) / len(valid_isbns), 4),
        "openlibrary_filled_fields": dict(sorted(openlibrary_fills.items())),
        "cover_record_count": cover_record_count,
        "cover_record_rate": round(cover_record_count / len(records), 4),
        "cover_providers": dict(sorted(cover_providers.items())),
        "cover_match_methods": dict(sorted(cover_match_methods.items())),
        "isbn_status": dict(sorted(isbn_status.items())),
        "raw_missing_fields": raw_missing_fields,
        "missing_fields": missing_fields,
        "raw_publisher_label_count": len(raw_publisher_labels),
        "normalized_publisher_count": len(publisher_values),
        "quality_flags": dict(sorted(quality_flags.items())),
        "remaining_review_records": [
            {
                "id": record["id"],
                "author": record.get("author", ""),
                "title": record.get("title", ""),
                "publication_year": record.get("publication_year", ""),
                "isbn_status": record["isbn_status"],
                "quality_flags": record["quality_flags"],
            }
            for record in records
            if any(
                flag in record["quality_flags"]
                for flag in (
                    "invalid_isbn",
                    "missing_isbn_1970_or_later",
                    "missing_isbn_unknown_year",
                    "missing_title",
                    "missing_author",
                    "missing_or_invalid_year",
                )
            )
        ],
        "applied_overrides": applied,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument(
        "--direct-cover-cache",
        type=Path,
        default=DEFAULT_DIRECT_COVER_CACHE,
    )
    parser.add_argument(
        "--openlibrary-cover-search",
        type=Path,
        default=DEFAULT_OPENLIBRARY_COVER_SEARCH,
    )
    parser.add_argument(
        "--google-cover-cache",
        type=Path,
        default=DEFAULT_GOOGLE_COVER_CACHE,
    )
    parser.add_argument(
        "--ellipses-cover-cache",
        type=Path,
        default=DEFAULT_ELLIPSES_COVER_CACHE,
    )
    parser.add_argument("--curation", type=Path, default=DEFAULT_CURATION)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    raw_payload = read_json(args.raw)
    openlibrary_cache = read_json(args.cache)
    direct_cover_cache = read_json(args.direct_cover_cache)
    openlibrary_cover_search = read_json(args.openlibrary_cover_search)
    google_cover_cache = read_json(args.google_cover_cache)
    ellipses_cover_cache = (
        read_json(args.ellipses_cover_cache)
        if args.ellipses_cover_cache.exists() else {"books": {}}
    )
    curation = read_json(args.curation)
    records = copy.deepcopy(raw_payload["records"])
    curated_on = str(curation.get("curated_on") or date.today().isoformat())

    openlibrary_matches = 0
    openlibrary_fills: Counter[str] = Counter()
    for record in records:
        provenance = record.setdefault("data_provenance", {})
        isbn = normalize_isbn(str(record.get("isbn", "")))
        if isbn and not valid_isbn(isbn):
            prefix = isbn[:13]
            if len(isbn) > 13 and valid_isbn13(prefix):
                isbn = prefix
        entry = openlibrary_cache.get(f"ISBN:{isbn}") if valid_isbn(isbn) else None
        if entry:
            openlibrary_matches += 1
            for field in fill_from_openlibrary(record, entry, provenance):
                openlibrary_fills[field] += 1
            record["openlibrary"] = openlibrary_summary(entry, curated_on)

        openlibrary_images = record.get("openlibrary", {}).get("cover", {})
        if openlibrary_images.get("medium"):
            record["cover"] = cover_summary(
                provider="Open Library",
                source_id="openlibrary_exact",
                retrieved_on=curated_on,
                match_method="exact_isbn",
                source_url=record["openlibrary"].get("url", ""),
                images=openlibrary_images,
            )

        direct_cover = direct_cover_cache.get("books", {}).get(isbn)
        if not record.get("cover") and direct_cover:
            record["cover"] = cover_summary(
                provider="Open Library",
                source_id="openlibrary_covers",
                retrieved_on=direct_cover_cache.get("retrieved_on", curated_on),
                match_method=direct_cover_cache.get("match_method", "exact_isbn"),
                source_url=direct_cover.get("source_url", ""),
                images=direct_cover.get("cover", {}),
            )

        google_isbn_cover = google_cover_cache.get("books", {}).get(isbn)
        if not record.get("cover") and google_isbn_cover:
            record["cover"] = cover_summary(
                provider="Google Books",
                source_id="google_books_dynamic",
                retrieved_on=google_cover_cache.get("retrieved_on", curated_on),
                match_method="exact_isbn",
                source_url=google_isbn_cover.get("info_url", ""),
                images=google_cover_images(google_isbn_cover.get("thumbnail_url", "")),
            )

        openlibrary_search_cover = openlibrary_cover_search.get("matches", {}).get(record["id"])
        if not record.get("cover") and openlibrary_search_cover:
            record["cover"] = cover_summary(
                provider="Open Library",
                source_id="openlibrary_cover_search",
                retrieved_on=openlibrary_search_cover.get("retrieved_on", curated_on),
                match_method=openlibrary_search_cover.get("match_method", ""),
                source_url=openlibrary_search_cover.get("source_url", ""),
                images=openlibrary_search_cover.get("cover", {}),
                confidence=openlibrary_search_cover.get("confidence", "high"),
            )

        google_identifier_cover = google_cover_cache.get("record_matches", {}).get(record["id"])
        if not record.get("cover") and google_identifier_cover:
            record["cover"] = cover_summary(
                provider="Google Books",
                source_id="google_books_dynamic",
                retrieved_on=google_cover_cache.get("retrieved_on", curated_on),
                match_method=google_identifier_cover.get("match_method", ""),
                source_url=google_identifier_cover.get("info_url", ""),
                images=google_cover_images(google_identifier_cover.get("thumbnail_url", "")),
            )

        ellipses_cover = ellipses_cover_cache.get("books", {}).get(isbn)
        if not record.get("cover") and ellipses_cover:
            record["cover"] = cover_summary(
                provider="Éditions Ellipses",
                source_id="ellipses_official",
                retrieved_on=ellipses_cover_cache.get("retrieved_on", curated_on),
                match_method="exact_isbn",
                source_url=ellipses_cover.get("source_url", ""),
                images=ellipses_cover.get("cover", {}),
            )
        if not provenance:
            record.pop("data_provenance", None)

    applied = apply_overrides(records, curation)
    classify_records(records)

    payload = {
        "source": raw_payload["source"],
        "curation": {
            "curated_on": curated_on,
            "raw_catalogue": str(args.raw.relative_to(ROOT)),
            "curation_rules": str(args.curation.relative_to(ROOT)),
            "openlibrary_snapshot": str(args.cache.relative_to(ROOT)),
            "openlibrary_direct_cover_snapshot": str(args.direct_cover_cache.relative_to(ROOT)),
            "openlibrary_cover_search_snapshot": str(args.openlibrary_cover_search.relative_to(ROOT)),
            "google_books_cover_snapshot": str(args.google_cover_cache.relative_to(ROOT)),
            "ellipses_cover_snapshot": str(args.ellipses_cover_cache.relative_to(ROOT)),
            "manual_override_count": len(applied),
            "policy": curation["policy"],
            "sources": curation["sources"],
        },
        "records": records,
    }
    report = build_quality_report(
        raw_payload["records"],
        records,
        applied,
        openlibrary_matches,
        openlibrary_fills,
        curated_on,
    )
    write_json(args.output, payload)
    write_json(args.report, report)
    print(
        f"Curated {len(records)} records; {len(applied)} manual overrides; "
        f"{openlibrary_matches} exact Open Library matches."
    )


if __name__ == "__main__":
    main()
