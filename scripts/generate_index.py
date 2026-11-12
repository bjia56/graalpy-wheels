#!/usr/bin/env python3
"""Generate the static PEP 503 index (to ./_site) from GitHub Release assets.

The index is derived state: nothing is committed after a build; the Pages
workflow regenerates it from releases every time.
"""
import html
import os
import pathlib
import shutil
import sys

import requests

from common import OWNER_REPO, ROOT, INDEX_URL, parse_tag
from normalize import normalize

OUT = ROOT / "_site"
STATIC = ROOT / "web"


def fetch_releases():
    headers = {"Accept": "application/vnd.github+json"}
    if os.environ.get("GITHUB_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['GITHUB_TOKEN']}"
    page = 1
    while True:
        r = requests.get(
            f"https://api.github.com/repos/{OWNER_REPO}/releases",
            params={"per_page": 100, "page": page}, headers=headers, timeout=30,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            return
        yield from batch
        page += 1


def collect():
    """-> {normalized_name: [(filename, url, sha256|None)]}"""
    pkgs = {}
    for rel in fetch_releases():
        if rel.get("draft") or not parse_tag(rel["tag_name"]):
            continue
        for a in rel["assets"]:
            if not a["name"].endswith(".whl"):
                continue
            # wheel filenames start with the distribution name
            dist = a["name"].split("-", 1)[0]
            digest = (a.get("digest") or "")
            sha = digest.split(":", 1)[1] if digest.startswith("sha256:") else None
            pkgs.setdefault(normalize(dist), []).append((a["name"], a["browser_download_url"], sha))
    return pkgs


def page(title: str, body: str, css: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="pypi:repository-version" content="1.0">
<title>{html.escape(title)}</title>
<link rel="stylesheet" href="{css}">
</head>
<body>
<main>
{body}
</main>
</body>
</html>
"""


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    shutil.copy(STATIC / "style.css", OUT / "style.css")

    pkgs = collect()

    # Root: one anchor per project (PEP 503)
    links = "\n".join(
        f'<li><a href="{n}/">{n}</a> <span class="count">{len(f)} file{"s" if len(f) != 1 else ""}</span></li>'
        for n, f in sorted(pkgs.items())
    )
    intro = (
        "<h1>graalpy-wheels</h1>"
        "<p>Prebuilt wheels for GraalPy on Linux x86_64.</p>"
        f"<pre>pip install --extra-index-url {INDEX_URL} &lt;package&gt;</pre>"
    )
    (OUT / "index.html").write_text(
        page("graalpy-wheels", f"{intro}<ul class=\"projects\">\n{links}\n</ul>", "style.css")
    )

    for name, files in pkgs.items():
        d = OUT / name
        d.mkdir()
        rows = []
        for fn, url, sha in sorted(files, reverse=True):
            frag = f"#sha256={sha}" if sha else ""
            rows.append(f'<li><a href="{html.escape(url)}{frag}">{html.escape(fn)}</a></li>')
        body = f'<p><a href="../">&larr; all packages</a></p><h1>{name}</h1><ul class="files">\n' + "\n".join(rows) + "\n</ul>"
        (d / "index.html").write_text(page(f"{name} · graalpy-wheels", body, "../style.css"))

    print(f"wrote {len(pkgs)} projects, {sum(len(f) for f in pkgs.values())} files to {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
