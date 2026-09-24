#!/usr/bin/env python3
"""Validate invariants of the curated library catalogue."""

from __future__ import annotations

import csv
import json
import re
import subprocess
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path

from extract_clz_library import extract_csv, preserve_record_ids
from fetch_openlibrary_cover_matches import select_identifiers, select_matches


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/library/clz-library-raw.json"
CURATION = ROOT / "data/library/library-curation.json"
NORMALIZATION = ROOT / "data/library/library-normalization.json"
THEMES = ROOT / "data/library/library-themes.json"
OUTPUT = ROOT / "assets/library/library-data.json"
REPORT = ROOT / "data/library/library-quality-report.json"
AUDIT = ROOT / "data/library/library-audit-artifact.json"
FRONTEND = ROOT / "assets/library/library.js"
ELLIPSES_COVERS = ROOT / "data/library/ellipses-cover-cache.json"
DUNOD_COVERS = ROOT / "data/library/dunod-cover-cache.json"
LALIBRAIRIE_COVERS = ROOT / "data/library/lalibrairie-cover-cache.json"
VERIFIED_COVERS = ROOT / "data/library/verified-cover-cache.json"
OPENLIBRARY_COVER_SEARCH = ROOT / "data/library/openlibrary-cover-search-cache.json"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_key(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value)
    ascii_value = "".join(
        character
        for character in ascii_value
        if not unicodedata.combining(character)
    ).casefold()
    return re.sub(r"[^a-z0-9]+", " ", ascii_value).strip()


def main() -> None:
    raw = read_json(RAW)
    curation = read_json(CURATION)
    normalization = read_json(NORMALIZATION)
    themes = read_json(THEMES)
    curated = read_json(OUTPUT)
    report = read_json(REPORT)
    audit = read_json(AUDIT)
    ellipses_covers = read_json(ELLIPSES_COVERS)
    dunod_covers = read_json(DUNOD_COVERS)
    lalibrairie_covers = read_json(LALIBRAIRIE_COVERS)
    verified_covers = read_json(VERIFIED_COVERS)
    openlibrary_cover_search = read_json(OPENLIBRARY_COVER_SEARCH)
    frontend = FRONTEND.read_text(encoding="utf-8")

    raw_records = raw["records"]
    records = curated["records"]
    assert len(raw_records) == 618
    assert len(records) == 602
    assert len({record["id"] for record in records}) == 602
    assert sum(record["source_record_count"] for record in records) == 618
    source_record_ids = [
        source_id
        for record in records
        for source_id in record["source_record_ids"]
    ]
    assert len(source_record_ids) == len(set(source_record_ids)) == 618
    assert set(source_record_ids) == {record["id"] for record in raw_records}
    assert all(record["id"] in record["source_record_ids"] for record in records)
    assert raw["source"]["name"] == "clz-books-2026-09-16.csv"
    assert raw["source"]["rows"] == 618
    assert raw["source"]["exported_on"] == "2026-09-16"
    assert raw["source"]["format"] == "CLZ Books CSV export"
    assert raw["source"]["previous_catalogue"] == (
        "pdf_book_2026-07-14_21-30-54.pdf"
    )
    assert raw["source"]["reconciliation"] == {
        "retained": 571,
        "added": 47,
        "removed": 0,
    }
    assert all(record["title"] for record in records)
    assert all(record["isbn_status"] != "invalid" for record in records)
    assert all("publisher_normalized" in record for record in records)
    assert all("author_normalized" in record for record in records)
    assert all(record["source_rows"] for record in records)
    rows = [row for record in records for row in record["source_rows"]]
    assert sorted(rows) == list(range(2, 620))
    csv_records = extract_csv(ROOT / "data/library/clz-books-2026-09-16.csv")
    for raw_record, csv_record in zip(raw_records, csv_records):
        assert {key: value for key, value in raw_record.items() if key != "id"} == {
            key: value for key, value in csv_record.items() if key != "id"
        }
    assert normalization["version"] == 1
    assert normalization["policy"]["preserve_distinct_valid_isbn"] is True
    theme_names = {category["name"] for category in themes["categories"]}
    theme_names.add(themes["policy"]["fallback"])
    assert all(record["theme"] in theme_names for record in records)
    assert sum(report["theme_counts"].values()) == len(records)
    assert Counter(record["theme"] for record in records) == report["theme_counts"]
    assert curated["curation"]["theme_rules"] == "data/library/library-themes.json"

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
        "valid": 464,
        "missing_pre_1970": 99,
        "missing_1970_or_later": 19,
        "missing_unknown_year": 20,
    }
    assert report["raw_record_count"] == 618
    assert report["record_count"] == 602
    assert report["source_record_count"] == 618
    assert report["duplicate_group_count"] == 16
    assert report["duplicate_records_collapsed_count"] == 16
    assert report["duplicate_reason_counts"] == {
        "compatible_bibliographic_metadata": 7,
        "same_valid_isbn": 9,
    }
    actual_duplicate_groups = {
        (frozenset(group["source_record_ids"]), group["reason"])
        for group in report["duplicate_groups"]
    }
    expected_duplicate_groups = {
        (frozenset({"book-0013", "book-0014"}), "compatible_bibliographic_metadata"),
        (frozenset({"book-0042", "book-0043"}), "compatible_bibliographic_metadata"),
        (frozenset({"book-0089", "book-0482"}), "same_valid_isbn"),
        (frozenset({"book-0111", "book-0207"}), "compatible_bibliographic_metadata"),
        (frozenset({"book-0162", "book-0163"}), "compatible_bibliographic_metadata"),
        (frozenset({"book-0173", "book-0174"}), "same_valid_isbn"),
        (frozenset({"book-0263", "book-0511"}), "same_valid_isbn"),
        (frozenset({"book-0279", "book-0280"}), "same_valid_isbn"),
        (frozenset({"book-0293", "book-0294"}), "compatible_bibliographic_metadata"),
        (frozenset({"book-0327", "book-0328"}), "same_valid_isbn"),
        (frozenset({"book-0360", "book-0361"}), "same_valid_isbn"),
        (frozenset({"book-0385", "book-0387"}), "same_valid_isbn"),
        (frozenset({"book-0408", "book-0409"}), "same_valid_isbn"),
        (frozenset({"book-0462", "book-0463"}), "same_valid_isbn"),
    }
    expected_duplicate_groups.update({
        (frozenset({"book-0583", "book-0584"}), "compatible_bibliographic_metadata"),
        (frozenset({"book-0592", "book-0593"}), "compatible_bibliographic_metadata"),
    })
    assert actual_duplicate_groups == expected_duplicate_groups
    assert report["normalized_publisher_count"] == 189
    assert report["normalization"] == {
        "author_record_change_count": 30,
        "publisher_record_change_count": 260,
        "duplicate_author_name_count_removed": 1,
    }
    assert report["unique_valid_isbn_count"] == 464
    assert report["openlibrary_unique_isbn_match_count"] == 317
    assert report["manual_override_count"] == len(curation["overrides"])
    assert report["cover_record_count"] == 454
    assert report["cover_record_rate"] == 0.7542
    assert report["cover_providers"] == {
        "AbeBooks": 43,
        "Anticariat.net": 1,
        "Dunod": 13,
        "Google Books": 51,
        "Internet Archive": 1,
        "LaLibrairie.com": 55,
        "Mir Titles": 1,
        "Open Library": 268,
        "Éditions Ellipses": 21,
    }
    assert sum(report["cover_match_methods"].values()) == 454
    assert ellipses_covers["requested_isbn_count"] == 27
    assert ellipses_covers["cover_count"] == 27
    assert not ellipses_covers["misses"]
    assert all(
        isbn == entry["isbn"] and isbn in entry["source_url"]
        for isbn, entry in ellipses_covers["books"].items()
    )
    assert dunod_covers["requested_isbn_count"] == 23
    assert dunod_covers["cover_count"] == 17
    assert len(dunod_covers["misses"]) == 6
    assert lalibrairie_covers["requested_isbn_count"] == 20
    assert lalibrairie_covers["cover_count"] == 68
    assert lalibrairie_covers["new_cover_count"] == 0
    assert len(lalibrairie_covers["misses"]) == 20
    assert all(
        isbn == entry["isbn"] and isbn in entry["source_url"]
        for isbn, entry in lalibrairie_covers["books"].items()
    )
    assert verified_covers["isbn_cover_count"] == 43
    assert verified_covers["record_cover_count"] == 4
    assert all(
        isbn == entry["isbn"] and isbn in entry["source_url"]
        for isbn, entry in verified_covers["books"].items()
    )
    assert set(verified_covers["record_matches"]) == {
        "book-0005",
        "book-0014",
        "book-0441",
        "book-0567",
    }
    assert "const externalUrl = coverSourceUrl || verifiedEditionUrl;" in frontend
    assert "openLibraryBookUrl" not in frontend

    by_id = {record["id"]: record for record in records}
    by_source_id = {
        source_id: record
        for record in records
        for source_id in record["source_record_ids"]
    }
    for override in curation["overrides"]:
        for field, value in override["changes"].items():
            assert by_source_id[override["id"]][field] == value
    valid_isbns = [
        record["isbn"] for record in records if record["isbn_status"] == "valid"
    ]
    assert len(valid_isbns) == len(set(valid_isbns)) == 464
    assert all(
        len({
            author.casefold().strip()
            for author in record["author_normalized"].split("|")
            if author.strip()
        })
        == len([
            author for author in record["author_normalized"].split("|")
            if author.strip()
        ])
        for record in records
    )
    canonical_labels: dict[tuple[str, str], str] = {}
    for record in records:
        entity_values = {
            "author": record["author_normalized"].split("|"),
            "publisher": [record["publisher_normalized"]],
        }
        for entity_type, values in entity_values.items():
            for value in values:
                label = value.strip()
                if not label:
                    continue
                key = (entity_type, normalized_key(label))
                assert canonical_labels.get(key, label) == label
                canonical_labels[key] = label
    assert by_id["book-0021"]["author_normalized"] == "Theodore W. Anderson"
    assert by_id["book-0022"]["author_normalized"] == "Theodore W. Anderson"
    assert by_id["book-0212"]["author_normalized"] == (
        "Trevor Hastie | Robert Tibshirani"
    )
    assert by_id["book-0243"]["author_normalized"] == "Jean-Étienne Rombaldi"
    assert by_id["book-0304"]["author_normalized"] == "Étienne Marceau"
    assert by_id["book-0475"]["author_normalized"] == (
        "Jean-Pierre Bélisle | Jacques Desrosiers"
    )
    assert by_id["book-0554"]["author_normalized"].startswith("Luc Adjengue |")
    assert by_id["book-0089"]["publisher_normalized"] == "Gaëtan Morin"
    assert by_id["book-0377"]["publisher_normalized"] == "Dunod"
    assert by_id["book-0432"]["publisher_normalized"] == "Wiley"
    assert by_id["book-0089"]["source_record_count"] == 2
    assert by_id["book-0089"]["source_record_ids"] == ["book-0482", "book-0089"]
    assert by_id["book-0279"]["source_record_count"] == 2
    assert by_id["book-0279"]["source_record_ids"] == ["book-0279", "book-0280"]
    assert by_id["book-0014"]["duplicate_group"]["reason"] == (
        "compatible_bibliographic_metadata"
    )
    frido_records = [record for record in records if record["title"] == "Le Frido 2021"]
    assert len(frido_records) == 4
    assert len({record["isbn"] for record in frido_records}) == 4
    assert report["preserved_distinct_isbn_group_count"] == 16
    audit_summary = audit["snapshot"]["datasets"]["summary"][0]
    assert audit_summary["records"] == 602
    assert audit_summary["source_records"] == 618
    assert audit_summary["normalized_publishers"] == 189
    assert len(audit["snapshot"]["datasets"]["review_cases"]) == 39
    assert by_id["book-0118"]["cover"]["provider"] == "Google Books"
    assert by_id["book-0118"]["cover"]["match_method"] == "title_author_year_publisher"
    assert by_id["book-0065"]["cover"]["provider"] == "Éditions Ellipses"
    assert by_id["book-0065"]["cover"]["match_method"] == "exact_isbn"
    assert by_id["book-0005"]["cover"]["provider"] == "Mir Titles"
    assert by_id["book-0014"]["cover"]["provider"] == "Anticariat.net"
    assert by_id["book-0158"]["cover"]["provider"] == "AbeBooks"
    assert by_id["book-0441"]["cover"]["provider"] == "Internet Archive"
    assert by_id["book-0567"]["cover"]["provider"] == "Google Books"
    assert by_id["book-0291"]["theme"] == "Informatique et science des données"
    assert by_id["book-0456"]["theme"] == "Statistique et probabilités"
    assert by_id["book-0567"]["theme"] == "Enseignement"
    assert by_id["book-0565"]["theme"] == "Physique et sciences"
    assert by_id["book-0118"]["theme"] == "Mathématiques"
    assert sum(not record.get("cover") for record in records) == 148
    assert sum(
        not record.get("cover") and record["isbn_status"] == "valid"
        for record in records
    ) == 31
    assert "book-0001" not in by_id
    assert by_id["book-0034"]["title"] == "Probabilité (L3M1)"
    previous_import_source_ids = {
        source_id
        for record in records
        for source_id in record["source_record_ids"]
        if 468 <= int(source_id.split("-")[1]) < 562
    }
    assert len(previous_import_source_ids) == 94
    previous_import_records = [
        record for record in records
        if any(
            source_id in previous_import_source_ids
            for source_id in record["source_record_ids"]
        )
    ]
    assert sum(bool(record.get("cover")) for record in previous_import_records) == 87
    latest_import_source_ids = {
        f"book-{number:04d}" for number in range(562, 573)
    }
    assert latest_import_source_ids <= set(source_record_ids)
    latest_import_records = [
        record for record in records
        if any(
            source_id in latest_import_source_ids
            for source_id in record["source_record_ids"]
        )
    ]
    assert len(latest_import_records) == 11
    assert sum(bool(record.get("cover")) for record in latest_import_records) == 1
    assert by_id["book-0563"]["isbn"] == "9782894220078"
    assert by_id["book-0565"]["title"].endswith("quasi-stationnaires")
    assert by_id["book-0571"]["publisher"].endswith("Saint-Jean-sur-Richelieu")
    assert by_id["book-0215"]["title"] == "Biographie des grands théorèmes"
    assert all(
        record.get("cover")
        for record in records
        if record["publisher_normalized"] == "Dunod"
        and record["isbn_status"] == "valid"
        and any(int(source_id.split("-")[1]) <= 572 for source_id in record["source_record_ids"])
    )

    rebuilt_matches = select_matches(
        records,
        openlibrary_cover_search["responses"],
        openlibrary_cover_search["retrieved_on"],
    )
    rebuilt_identifiers = select_identifiers(
        records,
        openlibrary_cover_search["responses"],
    )
    assert rebuilt_matches == openlibrary_cover_search["matches"]
    assert rebuilt_identifiers == openlibrary_cover_search["identifiers"]

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

    # New incomplete CLZ entries retain unknown years instead of guessed dates.
    assert by_id["book-0574"]["publication_year"] == ""
    assert by_id["book-0574"]["isbn_status"] == "missing_unknown_year"
    assert by_id["book-0600"]["title"] == "Transport Phenomena"
    assert by_id["book-0600"]["publication_year"] == "1960"
    assert all(f"book-{number:04d}" in source_record_ids for number in range(573, 620))
    assert by_id["book-0613"]["publisher"] == "McGraw-Hill"
    assert next(record for record in raw_records if record["id"] == "book-0613")["publisher"] == "1970"
    assert all(record["openlibrary"]["retrieved_on"] == "2026-07-14" for record in records if record.get("openlibrary"))
    assert report["generated_on"] == raw["source"]["imported_on"]
    assert audit["snapshot"]["generatedAt"] == report["generated_on"]

    with tempfile.TemporaryDirectory() as directory:
        temporary = Path(directory)
        # CSV parsing must preserve quoted Unicode titles and discard private columns.
        csv_path = temporary / "export.csv"
        with csv_path.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["Author", "Title", "ISBN", "Publisher", "Publication Date",
                             "Genre", "Publication Year", "Series", "Purchase Price", "Notes"])
            writer.writerow(["É. Auteur", 'Cours, volume "I"', "", "Éditions X", "1960",
                             "", "1960", "", "99.00", "Private note"])
        imported = extract_csv(csv_path)
        assert imported[0]["title"] == 'Cours, volume "I"'
        assert "Private note" not in json.dumps(imported)
        assert "99.00" not in json.dumps(imported)
        previous = [{**imported[0], "id": "book-0800", "publisher": "Éditions- X"}]
        imported[0]["publisher"] = "Éditions-X"
        assert preserve_record_ids(imported, previous) == {"retained": 1, "added": 0, "removed": 0}
        assert imported[0]["id"] == "book-0800"
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

    print(
        f"Library data validation passed: {len(records)} records, "
        "deterministic output, no invalid ISBN."
    )


if __name__ == "__main__":
    main()
