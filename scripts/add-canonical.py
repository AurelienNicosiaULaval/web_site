#!/usr/bin/env python3
"""Add canonical URLs after resource embedding, using Quarto's sitemap."""

from html import escape
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET


project = Path(__file__).resolve().parent.parent
output = project / "docs"
sitemap = output / "sitemap.xml"

# PDF-only renders may have no sitemap. Canonical links concern HTML pages.
if sitemap.exists():
    config = (project / "_quarto.yml").read_text(encoding="utf-8")
    match = re.search(r"^  site-url:\s*(\S+)\s*$", config, re.MULTILINE)
    if match is None:
        raise ValueError("The website needs a site-url.")
    base = urlsplit(match.group(1).strip("\"'"))
    prefix = base.path.rstrip("/") + "/"
    canonical = re.compile(
        r"<link\b(?=[^>]*\brel=['\"]canonical['\"])[^>]*>\s*",
        re.IGNORECASE,
    )
    count = 0
    for entry in ET.parse(sitemap).findall(".//{*}loc"):
        url = entry.text or ""
        parsed = urlsplit(url)
        if (parsed.scheme, parsed.netloc) != (base.scheme, base.netloc):
            raise ValueError(f"Unexpected sitemap origin: {url}")
        if not parsed.path.startswith(prefix):
            raise ValueError(f"Unexpected sitemap path: {url}")
        relative = unquote(parsed.path[len(prefix):])
        path = (output / relative).resolve()
        if not path.is_relative_to(output.resolve()):
            raise ValueError(f"Invalid sitemap path: {url}")
        if path.is_dir():
            path /= "index.html"
        if path.suffix != ".html":
            continue
        html = path.read_text(encoding="utf-8")
        html = canonical.sub("", html)
        link = f'<link rel="canonical" href="{escape(url, quote=True)}" data-external="1">\n'
        if "</head>" not in html:
            raise ValueError(f"Missing HTML head: {path}")
        path.write_text(html.replace("</head>", link + "</head>", 1), encoding="utf-8")
        count += 1
    print(f"Canonical URLs added to {count} sitemap pages.")
