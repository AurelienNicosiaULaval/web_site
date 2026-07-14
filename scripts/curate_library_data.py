#!/usr/bin/env python3
"""Curate the extracted CLZ catalogue without destroying its raw evidence.

The pipeline reads the immutable PDF extraction, fills only empty fields from
exact-ISBN Open Library records, applies manually sourced high-confidence
overrides, normalizes author and publisher labels, groups conservative duplicate
records, and emits both the public catalogue and a machine-readable quality
report.

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
DEFAULT_DUNOD_COVER_CACHE = ROOT / "data/library/dunod-cover-cache.json"
DEFAULT_LALIBRAIRIE_COVER_CACHE = ROOT / "data/library/lalibrairie-cover-cache.json"
DEFAULT_VERIFIED_COVER_CACHE = ROOT / "data/library/verified-cover-cache.json"
DEFAULT_CURATION = ROOT / "data/library/library-curation.json"
DEFAULT_NORMALIZATION = ROOT / "data/library/library-normalization.json"
DEFAULT_OUTPUT = ROOT / "assets/library/library-data.json"
DEFAULT_REPORT = ROOT / "data/library/library-quality-report.json"


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


def build_alias_map(values: dict[str, str], label: str) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for raw_value, canonical_value in values.items():
        key = normalize_text(raw_value)
        canonical = re.sub(r"\s+", " ", canonical_value).strip()
        if not key or not canonical:
            raise RuntimeError(f"Empty {label} normalization rule refused.")
        if key in aliases and aliases[key] != canonical:
            raise RuntimeError(
                f"Conflicting {label} normalization rule for {raw_value!r}."
            )
        aliases[key] = canonical
        aliases.setdefault(normalize_text(canonical), canonical)
    return aliases


def canonical_label(value: str, aliases: dict[str, str]) -> str:
    cleaned = re.sub(r"\s+", " ", value or "").strip()
    if not cleaned:
        return ""
    return aliases.get(normalize_text(cleaned), cleaned)


def split_authors(value: str) -> list[str]:
    return [
        re.sub(r"\s+", " ", author).strip()
        for author in re.split(r"\s*\|\s*", value or "")
        if author.strip()
    ]


def canonical_authors(value: str, aliases: dict[str, str]) -> tuple[str, int]:
    names: list[str] = []
    seen: set[str] = set()
    removed_duplicates = 0
    for raw_name in split_authors(value):
        canonical = canonical_label(raw_name, aliases)
        key = normalize_text(canonical)
        if key in seen:
            removed_duplicates += 1
            continue
        seen.add(key)
        names.append(canonical)
    return " | ".join(names), removed_duplicates


def normalize_entities(
    records: list[dict[str, Any]],
    normalization: dict[str, Any],
) -> dict[str, int]:
    author_aliases = build_alias_map(
        normalization.get("author_aliases", {}),
        "author",
    )
    publisher_aliases = build_alias_map(
        normalization.get("publisher_aliases", {}),
        "publisher",
    )
    author_changes = 0
    publisher_changes = 0
    duplicate_authors_removed = 0
    for record in records:
        author = str(record.get("author", ""))
        author_normalized, removed = canonical_authors(author, author_aliases)
        record["author_normalized"] = author_normalized
        duplicate_authors_removed += removed
        if author_normalized and author_normalized != author:
            author_changes += 1

        publisher = str(record.get("publisher", ""))
        normalized_publisher = canonical_label(publisher, publisher_aliases)
        record["publisher_normalized"] = normalized_publisher
        if normalized_publisher and normalized_publisher != publisher:
            publisher_changes += 1

    return {
        "author_record_change_count": author_changes,
        "publisher_record_change_count": publisher_changes,
        "duplicate_author_name_count_removed": duplicate_authors_removed,
    }


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
            normalize_text(
                str(record.get("author_normalized") or record.get("author", ""))
            ),
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

        record.setdefault(
            "publisher_normalized",
            re.sub(r"\s+", " ", str(record.get("publisher", ""))).strip(),
        )
        valid_record_isbn = record["isbn"] if record["isbn_status"] == "valid" else ""
        if valid_record_isbn and len(isbn_groups[valid_record_isbn]) > 1:
            flags.append("shared_isbn_possible_multiple_copy")

        title_author_key = (
            normalize_text(str(record.get("title", ""))),
            normalize_text(
                str(record.get("author_normalized") or record.get("author", ""))
            ),
        )
        if all(title_author_key) and len(title_author_groups[title_author_key]) > 1:
            flags.append("same_title_author_related_editions")
        record["quality_flags"] = flags


def author_identity_set(record: dict[str, Any]) -> set[str]:
    value = str(record.get("author_normalized") or record.get("author", ""))
    return {normalize_text(name) for name in split_authors(value) if normalize_text(name)}


def normalized_nonempty_values(
    records: list[dict[str, Any]],
    field: str,
) -> set[str]:
    return {
        normalize_text(str(record.get(field, "")))
        for record in records
        if str(record.get(field, "")).strip()
    }


def compatible_duplicate_component(records: list[dict[str, Any]]) -> bool:
    valid_isbns = {
        normalize_isbn(str(record.get("isbn", "")))
        for record in records
        if valid_isbn(normalize_isbn(str(record.get("isbn", ""))))
    }
    if len(valid_isbns) > 1:
        return False
    for field in ("publication_year", "publisher_normalized", "series"):
        if len(normalized_nonempty_values(records, field)) > 1:
            return False

    author_sets = [author_identity_set(record) for record in records]
    if any(not authors for authors in author_sets):
        return False
    for index, left in enumerate(author_sets):
        for right in author_sets[index + 1:]:
            if not (left <= right or right <= left):
                return False

    shared_evidence = any(
        sum(bool(str(record.get(field, "")).strip()) for record in records) > 1
        and len(normalized_nonempty_values(records, field)) == 1
        for field in ("isbn", "publication_year", "publisher_normalized", "series")
    )
    sparse_record = any(
        sum(
            bool(str(record.get(field, "")).strip())
            for field in ("isbn", "publication_year", "publisher_normalized", "series")
        ) == 0
        for record in records
    )
    return shared_evidence or sparse_record


def record_id_number(record: dict[str, Any]) -> int:
    match = re.search(r"(\d+)$", str(record.get("id", "")))
    return int(match.group(1)) if match else 10**9


def canonical_record_score(record: dict[str, Any]) -> tuple[int, ...]:
    return (
        1 if record.get("curation") else 0,
        1 if record.get("cover") else 0,
        sum(
            bool(record.get(field))
            for field in (
                "author", "title", "isbn", "publisher", "publication_date",
                "publication_year", "genre", "series",
            )
        ),
        len(author_identity_set(record)),
        len(str(record.get("title", ""))),
        len(str(record.get("author_normalized") or record.get("author", ""))),
        -record_id_number(record),
    )


def merge_duplicate_group(
    group: list[dict[str, Any]],
    reason: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ranked = sorted(group, key=canonical_record_score, reverse=True)
    merged = copy.deepcopy(ranked[0])
    mergeable_fields = (
        "author", "author_normalized", "title", "isbn", "publisher",
        "publisher_normalized", "publication_date", "publication_year",
        "genre", "series", "cover", "openlibrary", "data_provenance",
        "curation",
    )
    for candidate in ranked[1:]:
        for field in mergeable_fields:
            if not merged.get(field) and candidate.get(field):
                merged[field] = copy.deepcopy(candidate[field])

    source_record_ids = [record["id"] for record in group]
    source_pages = sorted({
        page
        for record in group
        for page in record.get("source_pages", [])
    })
    merged["source_record_count"] = sum(
        int(record.get("source_record_count", 1)) for record in group
    )
    merged["source_record_ids"] = source_record_ids
    merged["source_pages"] = source_pages
    merged["duplicate_group"] = {
        "reason": reason,
        "canonical_record_id": merged["id"],
        "source_record_ids": source_record_ids,
    }
    summary = {
        "canonical_record_id": merged["id"],
        "source_record_ids": source_record_ids,
        "source_record_count": merged["source_record_count"],
        "reason": reason,
        "isbn": merged.get("isbn", ""),
        "title": merged.get("title", ""),
        "author_normalized": merged.get("author_normalized", ""),
        "publisher_normalized": merged.get("publisher_normalized", ""),
        "publication_year": merged.get("publication_year", ""),
    }
    return merged, summary


def deduplicate_records(
    records: list[dict[str, Any]],
    policy: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    parents = list(range(len(records)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    def component(index: int) -> list[int]:
        root = find(index)
        return [candidate for candidate in range(len(records)) if find(candidate) == root]

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parents[right_root] = left_root

    if policy.get("merge_same_valid_isbn", True):
        isbn_groups: dict[str, list[int]] = defaultdict(list)
        for index, record in enumerate(records):
            isbn = normalize_isbn(str(record.get("isbn", "")))
            if valid_isbn(isbn):
                isbn_groups[isbn].append(index)
        for indices in isbn_groups.values():
            for index in indices[1:]:
                union(indices[0], index)

    if policy.get("merge_compatible_records", True):
        title_groups: dict[str, list[int]] = defaultdict(list)
        for index, record in enumerate(records):
            title = normalize_text(str(record.get("title", "")))
            if title:
                title_groups[title].append(index)
        for indices in title_groups.values():
            if len(indices) < 2:
                continue
            for left_position, left in enumerate(indices):
                for right in indices[left_position + 1:]:
                    if find(left) == find(right):
                        continue
                    combined_indices = sorted(set(component(left) + component(right)))
                    combined = [records[index] for index in combined_indices]
                    if compatible_duplicate_component(combined):
                        union(left, right)

    grouped_indices: dict[int, list[int]] = defaultdict(list)
    for index in range(len(records)):
        grouped_indices[find(index)].append(index)

    output: list[dict[str, Any]] = []
    duplicate_groups: list[dict[str, Any]] = []
    for indices in sorted(grouped_indices.values(), key=min):
        group = [records[index] for index in indices]
        if len(group) == 1:
            record = copy.deepcopy(group[0])
            record["source_record_count"] = int(
                record.get("source_record_count", 1)
            )
            record["source_record_ids"] = [record["id"]]
            output.append(record)
            continue

        valid_isbns = {
            normalize_isbn(str(record.get("isbn", "")))
            for record in group
            if valid_isbn(normalize_isbn(str(record.get("isbn", ""))))
        }
        reason = (
            "same_valid_isbn"
            if len(valid_isbns) == 1 and all(
                normalize_isbn(str(record.get("isbn", ""))) in valid_isbns
                for record in group
            )
            else "compatible_bibliographic_metadata"
        )
        merged, summary = merge_duplicate_group(group, reason)
        output.append(merged)
        duplicate_groups.append(summary)

    return output, duplicate_groups


def build_quality_report(
    raw_records: list[dict[str, Any]],
    records: list[dict[str, Any]],
    applied: list[dict[str, Any]],
    openlibrary_matches: int,
    openlibrary_fills: Counter[str],
    normalization_stats: dict[str, int],
    duplicate_groups: list[dict[str, Any]],
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
    raw_author_labels = {
        normalize_text(author)
        for record in raw_records
        for author in split_authors(str(record.get("author", "")))
        if normalize_text(author)
    }
    normalized_author_labels = {
        normalize_text(author)
        for record in records
        for author in split_authors(
            str(record.get("author_normalized") or record.get("author", ""))
        )
        if normalize_text(author)
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
    duplicate_reason_counts = Counter(
        group["reason"] for group in duplicate_groups
    )
    source_record_count = sum(
        int(record.get("source_record_count", 1)) for record in records
    )
    title_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        title_key = normalize_text(str(record.get("title", "")))
        if title_key:
            title_groups[title_key].append(record)
    preserved_distinct_isbn_groups = []
    for title_group in title_groups.values():
        distinct_isbns = sorted({
            record["isbn"]
            for record in title_group
            if record.get("isbn_status") == "valid"
        })
        if len(distinct_isbns) > 1:
            preserved_distinct_isbn_groups.append({
                "title": title_group[0].get("title", ""),
                "record_ids": [record["id"] for record in title_group],
                "isbns": distinct_isbns,
            })
    return {
        "generated_on": curated_on,
        "record_count": len(records),
        "raw_record_count": len(raw_records),
        "source_record_count": source_record_count,
        "unique_catalogue_record_count": len(records),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_source_record_count": sum(
            len(group["source_record_ids"]) for group in duplicate_groups
        ),
        "duplicate_records_collapsed_count": source_record_count - len(records),
        "duplicate_reason_counts": dict(sorted(duplicate_reason_counts.items())),
        "duplicate_groups": duplicate_groups,
        "preserved_distinct_isbn_group_count": len(
            preserved_distinct_isbn_groups
        ),
        "preserved_distinct_isbn_groups": preserved_distinct_isbn_groups,
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
        "raw_author_label_count": len(raw_author_labels),
        "normalized_author_count": len(normalized_author_labels),
        "normalization": normalization_stats,
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
    parser.add_argument(
        "--dunod-cover-cache",
        type=Path,
        default=DEFAULT_DUNOD_COVER_CACHE,
    )
    parser.add_argument(
        "--lalibrairie-cover-cache",
        type=Path,
        default=DEFAULT_LALIBRAIRIE_COVER_CACHE,
    )
    parser.add_argument(
        "--verified-cover-cache",
        type=Path,
        default=DEFAULT_VERIFIED_COVER_CACHE,
    )
    parser.add_argument("--curation", type=Path, default=DEFAULT_CURATION)
    parser.add_argument(
        "--normalization",
        type=Path,
        default=DEFAULT_NORMALIZATION,
    )
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
    dunod_cover_cache = (
        read_json(args.dunod_cover_cache)
        if args.dunod_cover_cache.exists() else {"books": {}}
    )
    lalibrairie_cover_cache = (
        read_json(args.lalibrairie_cover_cache)
        if args.lalibrairie_cover_cache.exists() else {"books": {}}
    )
    verified_cover_cache = (
        read_json(args.verified_cover_cache)
        if args.verified_cover_cache.exists()
        else {"books": {}, "record_matches": {}}
    )
    curation = read_json(args.curation)
    normalization = read_json(args.normalization)
    records = copy.deepcopy(raw_payload["records"])
    curated_on = str(curation.get("curated_on") or date.today().isoformat())
    applied = apply_overrides(records, curation)

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

        dunod_cover = dunod_cover_cache.get("books", {}).get(isbn)
        if not record.get("cover") and dunod_cover:
            record["cover"] = cover_summary(
                provider="Dunod",
                source_id="dunod_official",
                retrieved_on=dunod_cover_cache.get("retrieved_on", curated_on),
                match_method="exact_isbn",
                source_url=dunod_cover.get("source_url", ""),
                images=dunod_cover.get("cover", {}),
            )

        lalibrairie_cover = lalibrairie_cover_cache.get("books", {}).get(isbn)
        if not record.get("cover") and lalibrairie_cover:
            record["cover"] = cover_summary(
                provider="LaLibrairie.com",
                source_id="lalibrairie_exact",
                retrieved_on=lalibrairie_cover_cache.get("retrieved_on", curated_on),
                match_method="exact_isbn",
                source_url=lalibrairie_cover.get("source_url", ""),
                images=lalibrairie_cover.get("cover", {}),
            )

        verified_isbn_cover = verified_cover_cache.get("books", {}).get(isbn)
        if not record.get("cover") and verified_isbn_cover:
            record["cover"] = cover_summary(
                provider=verified_isbn_cover.get("provider", ""),
                source_id=verified_isbn_cover.get("source_id", ""),
                retrieved_on=verified_cover_cache.get("retrieved_on", curated_on),
                match_method=verified_isbn_cover.get("match_method", "exact_isbn"),
                source_url=verified_isbn_cover.get("source_url", ""),
                images=verified_isbn_cover.get("cover", {}),
            )

        verified_record_cover = verified_cover_cache.get("record_matches", {}).get(record["id"])
        if not record.get("cover") and verified_record_cover:
            record["cover"] = cover_summary(
                provider=verified_record_cover.get("provider", ""),
                source_id=verified_record_cover.get("source_id", ""),
                retrieved_on=verified_cover_cache.get("retrieved_on", curated_on),
                match_method=verified_record_cover.get(
                    "match_method", "title_author_year_publisher"
                ),
                source_url=verified_record_cover.get("source_url", ""),
                images=verified_record_cover.get("images", {}),
            )
        if not provenance:
            record.pop("data_provenance", None)

    normalization_stats = normalize_entities(records, normalization)
    classify_records(records)
    records, duplicate_groups = deduplicate_records(
        records,
        normalization.get("policy", {}),
    )
    classify_records(records)
    openlibrary_matches = sum(bool(record.get("openlibrary")) for record in records)
    openlibrary_fills = Counter(
        field
        for record in records
        for field, source in record.get("data_provenance", {}).items()
        if source == "openlibrary_exact"
    )

    payload = {
        "source": raw_payload["source"],
        "curation": {
            "curated_on": curated_on,
            "raw_catalogue": str(args.raw.relative_to(ROOT)),
            "curation_rules": str(args.curation.relative_to(ROOT)),
            "normalization_rules": str(args.normalization.relative_to(ROOT)),
            "openlibrary_snapshot": str(args.cache.relative_to(ROOT)),
            "openlibrary_direct_cover_snapshot": str(args.direct_cover_cache.relative_to(ROOT)),
            "openlibrary_cover_search_snapshot": str(args.openlibrary_cover_search.relative_to(ROOT)),
            "google_books_cover_snapshot": str(args.google_cover_cache.relative_to(ROOT)),
            "ellipses_cover_snapshot": str(args.ellipses_cover_cache.relative_to(ROOT)),
            "dunod_cover_snapshot": str(args.dunod_cover_cache.relative_to(ROOT)),
            "lalibrairie_cover_snapshot": str(args.lalibrairie_cover_cache.relative_to(ROOT)),
            "verified_cover_snapshot": str(args.verified_cover_cache.relative_to(ROOT)),
            "manual_override_count": len(applied),
            "raw_source_record_count": len(raw_payload["records"]),
            "catalogue_record_count": len(records),
            "source_record_count": sum(
                int(record.get("source_record_count", 1)) for record in records
            ),
            "duplicate_group_count": len(duplicate_groups),
            "policy": curation["policy"],
            "normalization_policy": normalization["policy"],
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
        normalization_stats,
        duplicate_groups,
        curated_on,
    )
    write_json(args.output, payload)
    write_json(args.report, report)
    print(
        f"Curated {len(records)} unique catalogue records from "
        f"{len(raw_payload['records'])} source records; "
        f"{len(duplicate_groups)} duplicate groups; {len(applied)} manual overrides; "
        f"{openlibrary_matches} exact Open Library matches."
    )


if __name__ == "__main__":
    main()
