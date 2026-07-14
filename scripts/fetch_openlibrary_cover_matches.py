#!/usr/bin/env python3
"""Find additional Open Library covers with strict bibliographic matching.

The exact-ISBN cache remains the preferred source. This script searches only
records that still lack a cover after the Open Library and Google Books ISBN
passes. Requests are grouped so the Search API is not used as a bulk backend.
Only title-author matches supported by an exact year and publisher, or by the
record ISBN, are retained.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
import urllib.error
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOGUE = ROOT / "assets/library/library-data.json"
DEFAULT_GOOGLE_CACHE = ROOT / "data/library/google-books-cover-cache.json"
DEFAULT_OUTPUT = ROOT / "data/library/openlibrary-cover-search-cache.json"
ENDPOINT = "https://openlibrary.org/search.json"
USER_AGENT = "AurelienNicosiaLibrary/1.0 (+https://aureliennicosiaulaval.github.io/web_site/)"
FIELDS = ",".join((
    "key", "title", "author_name", "first_publish_year", "publish_year",
    "publisher", "edition_count", "isbn", "cover_i", "cover_edition_key",
    "editions", "editions.key", "editions.title", "editions.publish_date",
    "editions.publisher", "editions.cover_i", "editions.isbn",
    "editions.oclc", "editions.lccn",
))
PUBLISHER_STOPWORDS = {
    "and", "co", "company", "de", "des", "du", "edition", "editions",
    "et", "inc", "la", "le", "les", "ltd", "press", "publishing",
    "the", "university",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    without_marks = "".join(
        character for character in normalized
        if not unicodedata.combining(character)
    )
    return re.sub(r"[^a-z0-9]+", " ", without_marks.casefold()).strip()


def title_matches(left: str, right: str) -> bool:
    return bool(normalize_text(left)) and normalize_text(left) == normalize_text(right)


def author_variants(value: str) -> list[str]:
    return [normalize_text(part) for part in re.split(r"\s*\|\s*", value) if normalize_text(part)]


def author_matches(record_author: str, candidate_authors: list[str]) -> bool:
    for record_name in author_variants(record_author):
        record_tokens = record_name.split()
        for candidate in candidate_authors:
            candidate_name = normalize_text(candidate)
            candidate_tokens = candidate_name.split()
            if record_name == candidate_name:
                return True
            if set(record_tokens) == set(candidate_tokens) and len(record_tokens) > 1:
                return True
            if record_tokens and candidate_tokens and record_tokens[-1] == candidate_tokens[-1]:
                if record_tokens[0][0] == candidate_tokens[0][0]:
                    return True
    return False


def publisher_tokens(value: str) -> set[str]:
    return {
        token for token in normalize_text(value).split()
        if token not in PUBLISHER_STOPWORDS and len(token) > 1
    }


def publisher_matches(record_publisher: str, candidates: list[str]) -> bool:
    record_tokens = publisher_tokens(record_publisher)
    if not record_tokens:
        return False
    for candidate in candidates:
        candidate_tokens = publisher_tokens(candidate)
        if not candidate_tokens:
            continue
        overlap = record_tokens & candidate_tokens
        if record_tokens <= candidate_tokens or candidate_tokens <= record_tokens:
            return True
        if len(overlap) / len(record_tokens | candidate_tokens) >= 0.5:
            return True
    return False


def years(values: Any) -> set[int]:
    if not isinstance(values, list):
        values = [values]
    parsed: set[int] = set()
    for value in values:
        match = re.search(r"\b(18|19|20)\d{2}\b", str(value or ""))
        if match:
            parsed.add(int(match.group(0)))
    return parsed


def escape_query(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def first_author(value: str) -> str:
    return re.split(r"\s*\|\s*", value or "", maxsplit=1)[0].strip()


def batched(values: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [values[index:index + size] for index in range(0, len(values), size)]


def fetch_batch(records: list[dict[str, Any]], timeout: float) -> dict[str, Any]:
    clauses = [
        f'(title:"{escape_query(record["title"])}" AND '
        f'author:"{escape_query(first_author(record["author"]))}")'
        for record in records
    ]
    query = " OR ".join(clauses)
    params = urllib.parse.urlencode({
        "q": query,
        "fields": FIELDS,
        "limit": min(100, max(20, len(records) * 10)),
    })
    request = urllib.request.Request(
        f"{ENDPOINT}?{params}",
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    return {
        "record_ids": [record["id"] for record in records],
        "query": query,
        "num_found": payload.get("numFound", payload.get("num_found", 0)),
        "docs": payload.get("docs", []),
    }


def fetch_batch_with_retry(
    records: list[dict[str, Any]],
    timeout: float,
    attempts: int,
) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return fetch_batch(records, timeout)
        except (TimeoutError, urllib.error.URLError) as error:
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(2 ** attempt)
    raise RuntimeError(
        f"Open Library request failed after {attempts} attempts"
    ) from last_error


def cover_urls(cover_id: int) -> dict[str, str]:
    base = f"https://covers.openlibrary.org/b/id/{cover_id}"
    return {
        "small": f"{base}-S.jpg",
        "medium": f"{base}-M.jpg",
        "large": f"{base}-L.jpg",
    }


def candidate_for(record: dict[str, Any], doc: dict[str, Any], retrieved_on: str) -> dict[str, Any] | None:
    if not title_matches(record.get("title", ""), doc.get("title", "")):
        return None
    if not author_matches(record.get("author", ""), doc.get("author_name", [])):
        return None

    record_year_values = years(record.get("publication_year", ""))
    record_year = next(iter(record_year_values), None)
    record_isbn = str(record.get("isbn", ""))
    work_isbns = {str(value) for value in doc.get("isbn", [])}
    work_years = years(doc.get("publish_year", []))
    work_publishers = [str(value) for value in doc.get("publisher", [])]
    exact_isbn = bool(record_isbn and record_isbn in work_isbns)
    year_match = record_year is not None and record_year in work_years
    publisher_match = publisher_matches(record.get("publisher_normalized", ""), work_publishers)

    edition_docs = doc.get("editions", {}).get("docs", [])
    edition_candidates: list[dict[str, Any]] = []
    for edition in edition_docs:
        cover_id = edition.get("cover_i")
        if not cover_id or not title_matches(record.get("title", ""), edition.get("title", "")):
            continue
        edition_isbns = {str(value) for value in edition.get("isbn", [])}
        edition_years = years(edition.get("publish_date", []))
        edition_publishers = [str(value) for value in edition.get("publisher", [])]
        edition_exact_isbn = bool(record_isbn and record_isbn in edition_isbns)
        edition_year_match = record_year is not None and record_year in edition_years
        edition_publisher_match = publisher_matches(
            record.get("publisher_normalized", ""), edition_publishers
        )
        if edition_exact_isbn:
            score = 120
            method = "exact_isbn_search"
        elif edition_year_match and edition_publisher_match:
            score = 95
            method = "title_author_year_publisher"
        else:
            continue
        edition_candidates.append({
            "score": score,
            "method": method,
            "cover_id": int(cover_id),
            "source_url": f"https://openlibrary.org{edition.get('key', '')}",
            "matched_year": sorted(edition_years),
            "matched_publishers": edition_publishers,
        })

    cover_id = doc.get("cover_i")
    if cover_id:
        if exact_isbn:
            score = 115
            method = "exact_isbn_search"
        elif year_match and publisher_match:
            score = 85
            method = "title_author_year_publisher_work"
        else:
            score = 0
            method = ""
        if score:
            cover_key = str(doc.get("cover_edition_key", ""))
            source_url = (
                f"https://openlibrary.org/books/{cover_key}"
                if cover_key else f"https://openlibrary.org{doc.get('key', '')}"
            )
            edition_candidates.append({
                "score": score,
                "method": method,
                "cover_id": int(cover_id),
                "source_url": source_url,
                "matched_year": sorted(work_years),
                "matched_publishers": work_publishers,
            })

    if not edition_candidates:
        return None
    edition_candidates.sort(key=lambda item: (-item["score"], item["cover_id"]))
    best = edition_candidates[0]
    return {
        "provider": "Open Library",
        "retrieved_on": retrieved_on,
        "match_method": best["method"],
        "confidence": "high",
        "score": best["score"],
        "cover_id": best["cover_id"],
        "source_url": best["source_url"],
        "matched_title": doc.get("title", ""),
        "matched_authors": doc.get("author_name", []),
        "matched_year": best["matched_year"],
        "matched_publishers": best["matched_publishers"],
        "cover": cover_urls(best["cover_id"]),
    }


def identifier_candidate_for(record: dict[str, Any], doc: dict[str, Any]) -> dict[str, Any] | None:
    if not title_matches(record.get("title", ""), doc.get("title", "")):
        return None
    if not author_matches(record.get("author", ""), doc.get("author_name", [])):
        return None

    record_year = next(iter(years(record.get("publication_year", ""))), None)
    record_isbn = str(record.get("isbn", ""))
    candidates: list[dict[str, Any]] = []
    for edition in doc.get("editions", {}).get("docs", []):
        if not title_matches(record.get("title", ""), edition.get("title", "")):
            continue
        edition_isbns = {str(value) for value in edition.get("isbn", [])}
        edition_years = years(edition.get("publish_date", []))
        edition_publishers = [str(value) for value in edition.get("publisher", [])]
        exact_isbn = bool(record_isbn and record_isbn in edition_isbns)
        year_match = record_year is not None and record_year in edition_years
        publisher_match = publisher_matches(
            record.get("publisher_normalized", ""), edition_publishers
        )
        if exact_isbn:
            score = 120
            method = "exact_isbn_search"
        elif year_match and publisher_match:
            score = 95
            method = "title_author_year_publisher"
        else:
            continue
        oclc = sorted({str(value) for value in edition.get("oclc", []) if str(value)})
        lccn = sorted({str(value) for value in edition.get("lccn", []) if str(value)})
        if not oclc and not lccn:
            continue
        candidates.append({
            "score": score,
            "match_method": method,
            "source_url": f"https://openlibrary.org{edition.get('key', '')}",
            "oclc": oclc,
            "lccn": lccn,
        })

    if not candidates:
        return None
    candidates.sort(key=lambda item: (-item["score"], item["source_url"]))
    best = candidates[0]
    tied_sources = {
        candidate["source_url"] for candidate in candidates
        if candidate["score"] == best["score"]
    }
    return best if len(tied_sources) == 1 else None


def select_matches(
    records: list[dict[str, Any]],
    responses: list[dict[str, Any]],
    retrieved_on: str,
) -> dict[str, Any]:
    by_id = {record["id"]: record for record in records}
    matches: dict[str, Any] = {}
    for response in responses:
        docs = response.get("docs", [])
        for record_id in response.get("record_ids", []):
            record = by_id[record_id]
            candidates = [
                candidate
                for doc in docs
                if (candidate := candidate_for(record, doc, retrieved_on)) is not None
            ]
            if not candidates:
                continue
            candidates.sort(key=lambda item: (-item["score"], item["cover_id"]))
            top = candidates[0]
            tied_ids = {
                candidate["cover_id"] for candidate in candidates
                if candidate["score"] == top["score"]
            }
            if len(tied_ids) == 1:
                matches[record_id] = top
    return matches


def select_identifiers(
    records: list[dict[str, Any]],
    responses: list[dict[str, Any]],
) -> dict[str, Any]:
    by_id = {record["id"]: record for record in records}
    identifiers: dict[str, Any] = {}
    for response in responses:
        docs = response.get("docs", [])
        for record_id in response.get("record_ids", []):
            record = by_id[record_id]
            candidates = [
                candidate
                for doc in docs
                if (candidate := identifier_candidate_for(record, doc)) is not None
            ]
            if not candidates:
                continue
            candidates.sort(key=lambda item: (-item["score"], item["source_url"]))
            top = candidates[0]
            tied_sources = {
                candidate["source_url"] for candidate in candidates
                if candidate["score"] == top["score"]
            }
            if len(tied_sources) == 1:
                identifiers[record_id] = top
    return identifiers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--google-cache", type=Path, default=DEFAULT_GOOGLE_CACHE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--pause", type=float, default=1.05)
    parser.add_argument("--attempts", type=int, default=3)
    parser.add_argument("--retrieved-on", default=str(date.today()))
    parser.add_argument("--reuse-responses", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    catalogue = read_json(args.catalogue)
    google_books = read_json(args.google_cache).get("books", {})
    records = catalogue["records"]
    targets = [
        record for record in records
        if record.get("title")
        and record.get("author")
        and not record.get("openlibrary", {}).get("cover", {}).get("medium")
        and not google_books.get(str(record.get("isbn", "")))
    ]

    responses: list[dict[str, Any]]
    if args.reuse_responses and args.output.exists():
        responses = read_json(args.output).get("responses", [])
    else:
        partial_path = args.output.with_suffix(".partial.json")
        responses = (
            read_json(partial_path).get("responses", [])
            if partial_path.exists() else []
        )
        completed_ids = {
            record_id
            for response in responses
            for record_id in response.get("record_ids", [])
        }
        remaining_targets = [
            record for record in targets if record["id"] not in completed_ids
        ]
        batches = batched(remaining_targets, args.batch_size)
        for index, batch in enumerate(batches):
            responses.append(fetch_batch_with_retry(batch, args.timeout, args.attempts))
            write_json(partial_path, {"responses": responses})
            if index + 1 < len(batches):
                time.sleep(args.pause)

    matches = select_matches(records, responses, args.retrieved_on)
    identifiers = select_identifiers(records, responses)
    payload = {
        "provider": "Open Library Search API",
        "retrieved_on": args.retrieved_on,
        "target_record_count": len(targets),
        "request_count": len(responses),
        "match_count": len(matches),
        "identifier_match_count": len(identifiers),
        "matches": matches,
        "identifiers": identifiers,
        "responses": responses,
    }
    write_json(args.output, payload)
    partial_path = args.output.with_suffix(".partial.json")
    if partial_path.exists():
        partial_path.unlink()
    print(
        f"Cached {len(matches)} strict Open Library cover matches for "
        f"{len(targets)} uncovered records in {len(responses)} grouped requests; "
        f"{len(identifiers)} edition identifier matches."
    )


if __name__ == "__main__":
    main()
