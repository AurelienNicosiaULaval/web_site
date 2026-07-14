#!/usr/bin/env python3
"""Cache LaLibrairie.com covers exposed at exact-ISBN image URLs.

The cache is a fallback for records still missing a cover after provider and
publisher-specific enrichment. Publisher-specific caches keep priority when
the catalogue is rebuilt.

Run from the project root:

    python3 scripts/fetch_lalibrairie_covers.py
"""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOGUE = ROOT / "assets/library/library-data.json"
DEFAULT_OUTPUT = ROOT / "data/library/lalibrairie-cover-cache.json"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0 Safari/537.36"
)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def cover_urls(isbn: str) -> dict[str, str]:
    folder = isbn[-3:]
    base = f"https://www.lalibrairie.com/cache/img/livres/{folder}/{isbn}"
    return {
        "small": f"{base}-xs.jpg",
        "medium": f"{base}.jpg",
        "large": f"{base}.jpg",
    }


def verified_image(url: str, timeout: float) -> bool:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get_content_type()
            payload = response.read()
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return False
        raise
    return content_type == "image/jpeg" and len(payload) >= 5_000 and payload.startswith(b"\xff\xd8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retrieved-on", default=str(date.today()))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    catalogue = read_json(args.catalogue)
    valid_isbns = {
        str(record.get("isbn", "")).strip()
        for record in catalogue["records"]
        if record.get("isbn_status") == "valid"
    }
    targets_by_isbn: dict[str, dict[str, str]] = {}
    for record in catalogue["records"]:
        isbn = str(record.get("isbn", "")).strip()
        if record.get("isbn_status") != "valid" or record.get("cover"):
            continue
        targets_by_isbn.setdefault(isbn, {
            "id": record["id"],
            "isbn": isbn,
            "title": str(record.get("title", "")).strip(),
        })
    targets = sorted(targets_by_isbn.values(), key=lambda record: record["isbn"])

    existing = read_json(args.output) if args.output.exists() else {"books": {}}
    books: dict[str, Any] = {
        isbn: entry
        for isbn, entry in existing.get("books", {}).items()
        if isbn in valid_isbns
    }
    initial_cover_count = len(books)
    misses: list[dict[str, str]] = []
    for target in targets:
        images = cover_urls(target["isbn"])
        if verified_image(images["medium"], args.timeout):
            books[target["isbn"]] = {
                "isbn": target["isbn"],
                "record_id": target["id"],
                "title": target["title"],
                "source_url": images["medium"],
                "cover": images,
            }
        else:
            misses.append(target)

    payload = {
        "provider": "LaLibrairie.com",
        "retrieved_on": args.retrieved_on,
        "match_method": "exact_isbn",
        "requested_isbn_count": len(targets),
        "cover_count": len(books),
        "new_cover_count": len(books) - initial_cover_count,
        "books": books,
        "misses": misses,
    }
    write_json(args.output, payload)
    print(
        f"Cache contains {len(books)} LaLibrairie.com covers; requested "
        f"{len(targets)} missing-cover ISBNs; added "
        f"{len(books) - initial_cover_count}; {len(misses)} were not found."
    )


if __name__ == "__main__":
    main()
