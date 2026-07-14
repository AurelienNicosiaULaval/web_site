#!/usr/bin/env python3
"""Cache Google Books cover thumbnails for exact ISBN matches.

Google Books Dynamic Links accepts multiple ISBNs in one request. The script
uses that batch endpoint, keeps only responses that include a cover thumbnail,
and writes a small deterministic cache consumed by ``curate_library_data.py``.

Run from the project root:

    python3 scripts/fetch_google_books_covers.py
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOGUE = ROOT / "assets/library/library-data.json"
DEFAULT_OPENLIBRARY_SEARCH = ROOT / "data/library/openlibrary-cover-search-cache.json"
DEFAULT_OUTPUT = ROOT / "data/library/google-books-cover-cache.json"
ENDPOINT = "https://books.google.com/books"
CALLBACK = "libraryCoverCallback"
USER_AGENT = "AurelienNicosiaLibrary/1.0 (+https://aureliennicosiaulaval.github.io/web_site/)"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def valid_isbn(value: str) -> bool:
    return bool(re.fullmatch(r"\d{9}[\dX]|\d{13}", value))


def isbn10_from_isbn13(value: str) -> str:
    if not re.fullmatch(r"978\d{10}", value):
        return ""
    body = value[3:12]
    total = sum((10 - index) * int(character) for index, character in enumerate(body))
    check = (11 - total % 11) % 11
    return body + ("X" if check == 10 else str(check))


def batched(values: list[str], size: int) -> list[list[str]]:
    return [values[index:index + size] for index in range(0, len(values), size)]


def parse_jsonp(payload: str) -> dict[str, Any]:
    prefix = f"{CALLBACK}("
    if not payload.startswith(prefix) or not payload.rstrip().endswith(");"):
        raise RuntimeError("Unexpected Google Books Dynamic Links response")
    return json.loads(payload[len(prefix):payload.rfind(");")])


def fetch_batch(bibkeys: list[str], timeout: float) -> dict[str, Any]:
    params = urllib.parse.urlencode({
        "bibkeys": ",".join(bibkeys),
        "jscmd": "viewapi",
        "callback": CALLBACK,
    })
    request = urllib.request.Request(
        f"{ENDPOINT}?{params}",
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return parse_jsonp(response.read().decode("utf-8"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument(
        "--openlibrary-search",
        type=Path,
        default=DEFAULT_OPENLIBRARY_SEARCH,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--batch-size", type=int, default=60)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--pause", type=float, default=0.2)
    parser.add_argument("--retrieved-on", default=str(date.today()))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    catalogue = read_json(args.catalogue)
    openlibrary_search = (
        read_json(args.openlibrary_search)
        if args.openlibrary_search.exists() else {"identifiers": {}}
    )
    isbns = sorted({
        str(record.get("isbn", "")).strip()
        for record in catalogue["records"]
        if record.get("isbn_status") == "valid"
        and valid_isbn(str(record.get("isbn", "")).strip())
    })

    isbn_aliases = {
        isbn: [isbn] + ([alias] if (alias := isbn10_from_isbn13(isbn)) else [])
        for isbn in isbns
    }
    isbn_keys = sorted({
        f"ISBN:{alias}"
        for aliases in isbn_aliases.values()
        for alias in aliases
    })
    external_keys = sorted({
        f"{kind.upper()}:{value}"
        for identifiers in openlibrary_search.get("identifiers", {}).values()
        for kind in ("oclc", "lccn")
        for value in identifiers.get(kind, [])
    })
    bibkeys = isbn_keys + external_keys

    responses: dict[str, Any] = {}
    batches = batched(bibkeys, args.batch_size)
    for index, batch in enumerate(batches):
        response = fetch_batch(batch, args.timeout)
        for bib_key, entry in response.items():
            thumbnail_url = str(entry.get("thumbnail_url", "")).replace("http://", "https://")
            if not thumbnail_url:
                continue
            responses[bib_key] = {
                "bib_key": bib_key,
                "info_url": str(entry.get("info_url", "")).replace("http://", "https://"),
                "preview": entry.get("preview", ""),
                "thumbnail_url": thumbnail_url,
            }
        if index + 1 < len(batches):
            time.sleep(args.pause)

    books: dict[str, Any] = {}
    for isbn, aliases in isbn_aliases.items():
        matched_key = next(
            (f"ISBN:{alias}" for alias in aliases if f"ISBN:{alias}" in responses),
            None,
        )
        if matched_key:
            books[isbn] = responses[matched_key]
    external_books = {
        bib_key: entry
        for bib_key, entry in responses.items()
        if not bib_key.startswith("ISBN:")
    }
    record_matches: dict[str, Any] = {}
    for record_id, identifiers in openlibrary_search.get("identifiers", {}).items():
        candidate_keys = [
            f"{kind.upper()}:{value}"
            for kind in ("oclc", "lccn")
            for value in identifiers.get(kind, [])
        ]
        matched_key = next(
            (key for key in candidate_keys if key in external_books),
            None,
        )
        if matched_key:
            record_matches[record_id] = {
                **external_books[matched_key],
                "match_method": identifiers["match_method"],
                "openlibrary_source_url": identifiers["source_url"],
            }

    payload = {
        "provider": "Google Books Dynamic Links",
        "retrieved_on": args.retrieved_on,
        "match_method": "exact_isbn",
        "requested_isbn_count": len(isbns),
        "requested_isbn_identifier_count": len(isbn_keys),
        "cover_count": len(books),
        "requested_external_identifier_count": len(external_keys),
        "external_cover_count": len(external_books),
        "record_identifier_cover_count": len(record_matches),
        "books": books,
        "external_books": external_books,
        "record_matches": record_matches,
    }
    write_json(args.output, payload)
    print(
        f"Cached {len(books)} Google Books ISBN covers for {len(isbns)} "
        f"distinct valid ISBNs and {len(record_matches)} edition-identifier covers."
    )


if __name__ == "__main__":
    main()
