#!/usr/bin/env python3
"""Validate invariants of the curated library catalogue."""

from __future__ import annotations

import json
import subprocess
import tempfile
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/library/clz-library-raw.json"
CURATION = ROOT / "data/library/library-curation.json"
OUTPUT = ROOT / "assets/library/library-data.json"
REPORT = ROOT / "data/library/library-quality-report.json"
FRONTEND = ROOT / "assets/library/library.js"
ELLIPSES_COVERS = ROOT / "data/library/ellipses-cover-cache.json"
DUNOD_COVERS = ROOT / "data/library/dunod-cover-cache.json"
LALIBRAIRIE_COVERS = ROOT / "data/library/lalibrairie-cover-cache.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    raw = read_json(RAW)
    curation = read_json(CURATION)
    curated = read_json(OUTPUT)
    report = read_json(REPORT)
    ellipses_covers = read_json(ELLIPSES_COVERS)
    dunod_covers = read_json(DUNOD_COVERS)
    lalibrairie_covers = read_json(LALIBRAIRIE_COVERS)
    frontend = FRONTEND.read_text(encoding="utf-8")

    raw_records = raw["records"]
    records = curated["records"]
    assert len(raw_records) == len(records) == 467
    assert [record["id"] for record in raw_records] == [record["id"] for record in records]
    assert len({record["id"] for record in records}) == 467
    assert all(record["title"] for record in records)
    assert all(record["isbn_status"] != "invalid" for record in records)
    assert all("publisher_normalized" in record for record in records)
    assert all(record["source_pages"] for record in records)

    source_ids = set(curation["sources"])
    for record in records:
        provenance = record.get("data_provenance", {})
        for value in provenance.values():
            assert set(value.split(",")) <= source_ids
        if record.get("curation"):
            assert set(record["curation"]["sources"]) <= source_ids
        if record.get("cover"):
            cover = record["cover"]
            assert cover["source_id"] in source_ids
            assert cover["confidence"] == "high"
            assert cover["source_url"].startswith("https://")
            assert cover["images"]["medium"].startswith("https://")

    status_counts = Counter(record["isbn_status"] for record in records)
    assert status_counts == {
        "valid": 368,
        "missing_pre_1970": 86,
        "missing_1970_or_later": 12,
        "missing_unknown_year": 1,
    }
    assert report["record_count"] == 467
    assert report["unique_valid_isbn_count"] == 360
    assert report["openlibrary_unique_isbn_match_count"] == 238
    assert report["manual_override_count"] == len(curation["overrides"])
    assert report["cover_record_count"] == 345
    assert report["cover_record_rate"] == 0.7388
    assert report["cover_providers"] == {
        "Dunod": 13,
        "Google Books": 41,
        "LaLibrairie.com": 49,
        "Open Library": 221,
        "Éditions Ellipses": 21,
    }
    assert sum(report["cover_match_methods"].values()) == 345
    assert ellipses_covers["requested_isbn_count"] == 21
    assert ellipses_covers["cover_count"] == 21
    assert not ellipses_covers["misses"]
    assert all(
        isbn == entry["isbn"] and isbn in entry["source_url"]
        for isbn, entry in ellipses_covers["books"].items()
    )
    assert dunod_covers["requested_isbn_count"] == 16
    assert dunod_covers["cover_count"] == 13
    assert len(dunod_covers["misses"]) == 3
    assert lalibrairie_covers["requested_isbn_count"] == 105
    assert lalibrairie_covers["cover_count"] == 62
    assert len(lalibrairie_covers["misses"]) == 43
    assert all(
        isbn == entry["isbn"] and isbn in entry["source_url"]
        for isbn, entry in lalibrairie_covers["books"].items()
    )
    assert "const externalUrl = coverSourceUrl || verifiedEditionUrl;" in frontend
    assert "openLibraryBookUrl" not in frontend

    by_id = {record["id"]: record for record in records}
    for override in curation["overrides"]:
        for field, value in override["changes"].items():
            assert by_id[override["id"]][field] == value
    assert by_id["book-0118"]["cover"]["provider"] == "Google Books"
    assert by_id["book-0118"]["cover"]["match_method"] == "title_author_year_publisher"
    assert by_id["book-0065"]["cover"]["provider"] == "Éditions Ellipses"
    assert by_id["book-0065"]["cover"]["match_method"] == "exact_isbn"
    assert by_id["book-0215"]["title"] == "Biographie des grands théorèmes"
    assert all(
        record.get("cover")
        for record in records
        if record["publisher_normalized"] == "Dunod"
        and record["isbn_status"] == "valid"
    )

    record_order = {record["id"]: index for index, record in enumerate(records)}
    rarity_candidates = sorted(
        (
            record
            for record in records
            if record.get("isbn_status") == "missing_pre_1970"
            and record.get("title")
            and record.get("author")
            and record.get("publisher_normalized")
        ),
        key=lambda record: (int(record["publication_year"]), record_order[record["id"]]),
    )
    assert [record["id"] for record in rarity_candidates[:5]] == [
        "book-0118",
        "book-0267",
        "book-0088",
        "book-0205",
        "book-0122",
    ]

    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        generated_output = temporary / "library-data.json"
        generated_report = temporary / "quality-report.json"
        subprocess.run(
            [
                "python3",
                str(ROOT / "scripts/curate_library_data.py"),
                "--output",
                str(generated_output),
                "--report",
                str(generated_report),
            ],
            cwd=ROOT,
            check=True,
        )
        assert generated_output.read_bytes() == OUTPUT.read_bytes()
        assert generated_report.read_bytes() == REPORT.read_bytes()

    print("Library data validation passed: 467 records, deterministic output, no invalid ISBN.")


if __name__ == "__main__":
    main()
