#!/usr/bin/env python3
"""Cache official Éditions Ellipses covers matched by exact ISBN.

The script targets Ellipses records that still have no cover after the Open
Library and Google Books enrichment. Each retained result must contain the
catalogue ISBN in the publisher's product card.

Run from the project root:

    python3 scripts/fetch_ellipses_covers.py
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
DEFAULT_OUTPUT = ROOT / "data/library/ellipses-cover-cache.json"
SEARCH_ENDPOINT = "https://www.editions-ellipses.fr/fr/recherche"
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
    articles = re.findall(
        r'<article\s+class="product-category[^>]*>.*?</article>',
        payload,
        flags=re.DOTALL | re.IGNORECASE,
    )
    exact_article = next(
        (
            article
            for article in articles
            if isbn in re.sub(r"\D", "", html.unescape(article))
        ),
        None,
    )
    if not exact_article:
        return None

    source_match = re.search(
        r'<a\s+class="img-link"\s+href="([^"]+)"',
        exact_article,
        flags=re.IGNORECASE,
    )
    image_match = re.search(
        r'<img[^>]+class="js-qv-product-cover"[^>]+src="([^"]+)"[^>]+alt="([^"]*)"',
        exact_article,
        flags=re.IGNORECASE,
    )
    if not source_match or not image_match:
        return None

    source_url = urllib.parse.urljoin(SEARCH_ENDPOINT, html.unescape(source_match.group(1)))
    source_url = source_url.split("#", maxsplit=1)[0]
    list_image = html.unescape(image_match.group(1))
    if "-liste_image/" not in list_image:
        return None

    home_image = list_image.replace("-liste_image/", "-home_default/")
    large_image = list_image.replace("-liste_image/", "-large_modale_produit/")
    return {
        "isbn": isbn,
        "title": html.unescape(image_match.group(2)).strip(),
        "source_url": source_url,
        "cover": {
            "small": home_image,
            "medium": home_image,
            "large": large_image,
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
            if record.get("publisher_normalized") == "Ellipses"
            and record.get("isbn_status") == "valid"
            and not record.get("cover")
        ),
        key=lambda record: record["isbn"],
    )

    books: dict[str, Any] = {}
    misses: list[dict[str, str]] = []
    for index, target in enumerate(targets):
        query = urllib.parse.urlencode({"controller": "search", "s": target["isbn"]})
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
        "provider": "Éditions Ellipses",
        "retrieved_on": args.retrieved_on,
        "match_method": "exact_isbn",
        "requested_isbn_count": len(targets),
        "cover_count": len(books),
        "books": books,
        "misses": misses,
    }
    write_json(args.output, payload)
    print(
        f"Cached {len(books)} official Ellipses covers for {len(targets)} "
        f"missing-cover ISBNs; {len(misses)} ISBNs were not found."
    )


if __name__ == "__main__":
    main()
