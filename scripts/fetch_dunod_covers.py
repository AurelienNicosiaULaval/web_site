#!/usr/bin/env python3
"""Cache official Dunod covers matched by exact ISBN.

Every valid Dunod ISBN is checked so a catalogue refresh cannot erase an
official cover merely because another provider already supplies an image.

Run from the project root:

    python3 scripts/fetch_dunod_covers.py
"""

from __future__ import annotations

import argparse
import html
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
DEFAULT_OUTPUT = ROOT / "data/library/dunod-cover-cache.json"
SEARCH_ENDPOINT = "https://www.dunod.com/recherche"
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


def fetch_html(url: str, timeout: float) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_exact_isbn_result(payload: str, isbn: str) -> dict[str, Any] | None:
    marker = f'data-sku="{isbn}"'
    marker_position = payload.find(marker)
    if marker_position < 0:
        return None

    window_start = max(0, payload.rfind('<div id="node-', 0, marker_position))
    result = payload[window_start:marker_position + len(marker)]
    source_matches = re.findall(r'<a\s+href="([^"]+)"', result, flags=re.IGNORECASE)
    image_matches = re.findall(
        r'<img[^>]+src="([^"]+)"[^>]+alt="([^"]*)"',
        result,
        flags=re.IGNORECASE,
    )
    if not source_matches or not image_matches:
        return None

    source_url = urllib.parse.urljoin(SEARCH_ENDPOINT, html.unescape(source_matches[-1]))
    medium_image, title = image_matches[-1]
    medium_image = html.unescape(medium_image)
    title = html.unescape(title).strip()
    if isbn not in medium_image or "/styles/moyen_desktop/" not in medium_image:
        return None

    return {
        "isbn": isbn,
        "title": title,
        "source_url": source_url,
        "cover": {
            "small": medium_image.replace("/styles/moyen_desktop/", "/styles/petit_desktop/"),
            "medium": medium_image,
            "large": medium_image.replace("/styles/moyen_desktop/", "/styles/grand_desktop/"),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalogue", type=Path, default=DEFAULT_CATALOGUE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--pause", type=float, default=0.5)
    parser.add_argument("--retrieved-on", default=str(date.today()))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    catalogue = read_json(args.catalogue)
    targets = sorted(
        (
            {
                "id": record["id"],
                "isbn": str(record.get("isbn", "")).strip(),
                "title": str(record.get("title", "")).strip(),
            }
            for record in catalogue["records"]
            if record.get("publisher_normalized") == "Dunod"
            and record.get("isbn_status") == "valid"
        ),
        key=lambda record: record["isbn"],
    )

    books: dict[str, Any] = {}
    misses: list[dict[str, str]] = []
    for index, target in enumerate(targets):
        query = urllib.parse.urlencode({"text": target["isbn"]})
        result = parse_exact_isbn_result(
            fetch_html(f"{SEARCH_ENDPOINT}?{query}", args.timeout),
            target["isbn"],
        )
        if result:
            books[target["isbn"]] = {**result, "record_id": target["id"]}
        else:
            misses.append(target)
        if index + 1 < len(targets):
            time.sleep(args.pause)

    payload = {
        "provider": "Dunod",
        "retrieved_on": args.retrieved_on,
        "match_method": "exact_isbn",
        "requested_isbn_count": len(targets),
        "cover_count": len(books),
        "books": books,
        "misses": misses,
    }
    write_json(args.output, payload)
    print(
        f"Cached {len(books)} official Dunod covers for {len(targets)} "
        f"exact ISBNs; {len(misses)} ISBNs were not found."
    )


if __name__ == "__main__":
    main()
