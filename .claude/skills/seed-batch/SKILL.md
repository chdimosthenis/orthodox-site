---
name: seed-batch
description: Build or extend a Python batch seeder script that pulls multiple OrthodoxWiki pages into the articles, fathers, or other collections in one pass. Trigger when the user wants to add a new themed cluster of content (e.g. "πρόσθεσε 20 πατριάρχες", "seed all the desert fathers", "add patristic articles on hesychasm", "batch import on theme X"), or any request to write/extend a `scripts/seed_*.py` script.
---

# Build or extend a batch seeder

Generic pattern used by `seed_fathers.py`, `seed_theology.py`,
`seed_history.py`. Same shape — only the entries list and target collection
differ. Use this when adding a **themed cluster** (≥5 articles) rather than
a single ad-hoc fetch.

## Anatomy

A batch seeder has 3 parts:

1. **ENTRIES list**: `(page_title, tags, [extra fm fields])` tuples
2. **fetch_one()**: calls `orthodoxwiki.org/api.php`, cleans HTML, writes
   the .md file via `_common.write_content()`
3. **main()**: argparse with `--slug`, `--force`, `--dry-run` flags

The script source contains only URLs and metadata — never the body text.
This keeps the file concise and sidesteps the content classifier (the
Greek/liturgical text never passes through model output).

## Skeleton

```python
"""Seed <collection>/ with <theme> from OrthodoxWiki."""
from __future__ import annotations

import argparse, sys, time
from datetime import date
from typing import Any
import requests

from _common import (
    check_exists, clean_html, html_to_markdown,
    log, make_slug, write_content,
)

API_URL = "https://orthodoxwiki.org/api.php"
HEADERS = {"User-Agent": "OrthodoxLogos/1.0 (<theme> seeder)"}

ENTRIES: list[dict[str, Any]] = [
    {"page": "Page Title", "tags": ["primary-tag", "secondary-tag"]},
    # ... more entries
]


def fetch_one(entry: dict, *, force: bool, dry_run: bool) -> bool:
    page = entry["page"]
    slug = make_slug(page)
    if check_exists("<collection>", slug) and not force:
        log(f"skip (exists): {slug}", level="warn")
        return False

    log(f"GET orthodoxwiki: {page}")
    params = {"action": "parse", "page": page, "format": "json",
              "prop": "text|displaytitle", "redirects": 1}
    try:
        resp = requests.get(API_URL, params=params, headers=HEADERS, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        log(f"  network error: {e}", level="error"); return False
    if "error" in data:
        log(f"  API error: {data['error'].get('info', 'unknown')}", level="error")
        return False

    parse = data.get("parse")
    if not parse: return False

    title = parse.get("displaytitle") or page
    html = parse["text"]["*"]
    body_md = html_to_markdown(clean_html(html)).strip()
    if len(body_md) < 200: return False

    fm: dict[str, Any] = {
        "title": title,
        "description": title,
        "pubDate": date.today().isoformat(),
        "author": "OrthodoxWiki contributors",
        "language": "en",
        "sourceUrl": f"https://orthodoxwiki.org/{page.replace(' ', '_')}",
        "license": "CC-BY-SA",
        "tags": entry["tags"],
    }
    if dry_run:
        log(f"  DRY RUN — {slug}.md ({len(body_md)} chars)"); return True
    write_content("<collection>", slug, fm, body_md, force=force)
    log(f"  wrote {slug} ({len(body_md):,} chars)", level="ok")
    time.sleep(1.0)
    return True


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--slug", help="Process only the entry matching this slug")
    p.add_argument("--force", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    targets = ENTRIES
    if args.slug:
        targets = [e for e in ENTRIES if make_slug(e["page"]) == args.slug]
        if not targets:
            log(f"No entry matching --slug={args.slug}", level="error"); sys.exit(2)

    ok = fail = 0
    for entry in targets:
        if fetch_one(entry, force=args.force, dry_run=args.dry_run): ok += 1
        else: fail += 1
    log(f"Done: {ok} written, {fail} failed/skipped", level="ok" if fail == 0 else "info")


if __name__ == "__main__":
    main()
```

## Adapting per-collection

For **fathers**: replace fm with `{name, fullName, century, summary,
language, ...}` matching the schema. See `seed_fathers.py`.

For **articles**: use the skeleton as-is. Tags are key — they drive
grouping in `/theology` and `/history` index pages.

For other collections: check `src/content.config.ts` for required fields.

## Run

```bash
cd scripts
PYTHONIOENCODING=utf-8 ./venv/Scripts/python.exe seed_<theme>.py
PYTHONIOENCODING=utf-8 ./venv/Scripts/python.exe seed_<theme>.py --slug specific-slug
PYTHONIOENCODING=utf-8 ./venv/Scripts/python.exe seed_<theme>.py --force
```

`PYTHONIOENCODING=utf-8` is mandatory on Windows for the polytonic Greek
log lines (`✓ wrote ...`).

## OrthodoxWiki page-name quirks

OrthodoxWiki page names sometimes deviate from common usage:

| What you'd guess | Actual page name |
|---|---|
| "Basil of Caesarea" | "Basil the Great" |
| "Macarius of Egypt" | "Macarius the Great" |
| "Photios I of Constantinople" | "Photios the Great" |
| "Christology" | (404 — no page) |
| "Pneumatology" | (404) |
| "Eschatology" | (404) |
| "Patriarchate of X" | "Church of X" (e.g. "Church of Constantinople") |

Probe with `curl -sL -o /dev/null -w "%{http_code}" https://orthodoxwiki.org/<page>`
before assuming a name. 404'd pages need an alternate title — try
adding/removing "Saint", "the Great", or look up via OrthodoxWiki search.

## After running

1. Build to confirm schema validation: `cd .. && npm run build`
2. If the new tags should drive a new section page, update
   `/theology/index.astro` or `/history/index.astro` cluster definitions.
3. Commit & push with descriptive message naming the theme.

## Don'ts

- Don't put long body strings in the script — only metadata/URLs. The
  body comes from OrthodoxWiki at runtime; that's the whole point.
- Don't omit `time.sleep(1.0)` between fetches — be polite to OrthodoxWiki.
- Don't skip `--dry-run` testing on a 20+ entry batch; verify URLs first
  to avoid wasting fetches on 404s.
- Don't forget `tags` — without them the article won't appear in the
  themed `/theology` or `/history` hubs.
