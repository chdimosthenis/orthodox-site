"""Fetch full-year Greek Orthodox synaxari from apostoliki-diakonia.gr.

Source: https://apostoliki-diakonia.gr/eortologio/{month}/
Strategy: fetch the 12 month-overview WP posts via REST API; each contains
a table with one row per day (day-number, brief saint list, outbound link
to either the full day page or the calendar-icon image). We emit one JSON
file keyed by MM-DD that the home-page TodaysEortologio widget reads at
build time. Run once per year; site rebuilds daily already advance "today".

Output: src/data/synaxari.json
Usage:  PYTHONIOENCODING=utf-8 ./venv/Scripts/python.exe fetch_synaxari.py
"""
from _common import log
from pathlib import Path
import json
import re
import sys
import time
from typing import Optional

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "data" / "synaxari.json"
UA = "orthodoxoskomvos.gr-synaxari-fetch/1.0 (+https://orthodoxoskomvos.gr)"

# Month-overview WP post slugs and their MM index. Confirmed by probing
# /wp-json/wp/v2/eortologio: month overview slugs are English lowercase.
MONTHS = [
    ("january",   1, "Ἰανουαρίου"),
    ("february",  2, "Φεβρουαρίου"),
    ("march",     3, "Μαρτίου"),
    ("april",     4, "Ἀπριλίου"),
    ("may",       5, "Μαΐου"),
    ("june",      6, "Ἰουνίου"),
    ("july",      7, "Ἰουλίου"),
    ("august",    8, "Αὐγούστου"),
    ("september", 9, "Σεπτεμβρίου"),
    ("october",  10, "Ὀκτωβρίου"),
    ("november", 11, "Νοεμβρίου"),
    ("december", 12, "Δεκεμβρίου"),
]

BASE = "https://apostoliki-diakonia.gr"
SITE_HOST = "apostoliki-diakonia.gr"
DAY_RE = re.compile(r"^\s*(\d{1,2})\b")

# Source has a handful of editor mojibake instances where a polytonic
# capital alpha (Ἅ / Ἀ / Ἄ) was replaced by U+20BC (₼, manat sign). All
# four observed cases (Τα ₼για / μάρτυρος ₼σσαντ / μάρτυρος ₼ννης /
# Αγίου ₼σκιοτ) sit in monotonic context — Ά (U+0386) is the safe fix.
NAME_NORMALIZE = [
    ("₼", "Ά"),  # ₼ → Ά
]


def _normalize_names(text: str) -> str:
    for old, new in NAME_NORMALIZE:
        text = text.replace(old, new)
    # Tidy stray whitespace around commas (source has " , " separators)
    text = re.sub(r"\s+,", ",", text)
    text = re.sub(r",\s*", ", ", text)
    text = re.sub(r"\s+", " ", text).strip(" ,;")
    return text


def fetch_month(slug: str) -> dict:
    """Fetch a month-overview post by slug via WP REST API."""
    url = f"{BASE}/wp-json/wp/v2/eortologio"
    r = requests.get(
        url,
        params={"slug": slug, "per_page": 1},
        headers={"User-Agent": UA, "Accept": "application/json"},
        timeout=30,
    )
    r.raise_for_status()
    items = r.json()
    if not items:
        raise RuntimeError(f"No WP entry found for slug={slug}")
    return items[0]


def _absolutize(href: str) -> str:
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return BASE + href
    return f"{BASE}/{href}"


def _classify_link(href: Optional[str]) -> Optional[str]:
    """Return absolute URL only if it's a real day-page on the same site,
    not a calendar-icon image upload. Image links are pointers to a JPG of
    the printed calendar — not useful as outbound links for readers."""
    if not href:
        return None
    href = href.strip()  # May entries have leading whitespace in href
    if not href:
        return None
    abs_url = _absolutize(href)
    # Reject image uploads; keep only HTML pages on the site itself.
    if "/wp-content/uploads/" in abs_url:
        return None
    if SITE_HOST not in abs_url:
        return None
    if re.search(r"\.(jpe?g|png|gif|webp)(\?.*)?$", abs_url, re.I):
        return None
    # Strip empty trailing fragment ("page/#" → "page/").
    abs_url = re.sub(r"#$", "", abs_url)
    return abs_url


def parse_month_content(html: str, month_idx: int, month_overview_url: str) -> list[dict]:
    """Extract one row per day from a month-overview WP post.

    Layouts seen in the wild:
      * `<table><tr><td><strong>{day} {month}</strong><br/><a/></td></tr>`
        (Feb, Mar, Jun-Dec) — one <tr> per day
      * `<p align=...><strong>{day} {month}</strong><br/><a/>...</p>`
        (Jan, Apr) — one <p> per day
      * `<div align=...><strong>{day} {month}</strong><br/><a/>...</div>`
        (May) — one <div> per day

    Universal strategy: iterate <tr> if the post has a table, else iterate
    <p> and <div>. For each candidate block, concatenate all <strong> text
    and accept it as a day-row if it starts with 1-31."""
    soup = BeautifulSoup(html, "html.parser")
    has_table = soup.find("table") is not None
    blocks = soup.find_all("tr") if has_table else soup.find_all(["p", "div"])

    rows: dict[int, dict] = {}
    for block in blocks:
        strongs = block.find_all("strong")
        if not strongs:
            continue
        strong_text = " ".join(s.get_text(" ", strip=True) for s in strongs)
        strong_text = re.sub(r"\s+", " ", strong_text).strip()
        m = DAY_RE.match(strong_text)
        if not m:
            continue
        day = int(m.group(1))
        if not (1 <= day <= 31) or day in rows:
            continue
        clone = BeautifulSoup(str(block), "html.parser")
        for s in clone.find_all("strong"):
            s.decompose()
        for br in clone.find_all("br"):
            br.replace_with("\n")
        text = re.sub(r"\s+", " ", clone.get_text(" ", strip=True)).strip(" ,;")
        text = _normalize_names(text)
        if not text:
            continue
        link = None
        for a in clone.find_all("a"):
            link = _classify_link(a.get("href"))
            if link:
                break
        rows[day] = {"day": day, "names": text, "url": link or month_overview_url}
    return sorted(rows.values(), key=lambda r: r["day"])


def main() -> int:
    by_date: dict[str, dict] = {}
    for slug, mm, _label in MONTHS:
        log(f"Fetching month: {slug}")
        item = fetch_month(slug)
        overview_url = item["link"]
        html = item["content"]["rendered"]
        rows = parse_month_content(html, mm, overview_url)
        log(f"  parsed {len(rows)} day rows")
        for row in rows:
            key = f"{mm:02d}-{row['day']:02d}"
            if key in by_date:
                # Same day defined twice in one month would be a parser bug.
                log(f"  WARN: duplicate key {key}; keeping first")
                continue
            by_date[key] = {
                "names": row["names"],
                "url": row["url"],
            }
        time.sleep(1.5)  # be polite

    # Sanity: report coverage. Leap-year Feb 29 may or may not be present.
    expected = sum(days for _, _, days in [
        ("jan", 1, 31), ("feb", 2, 29), ("mar", 3, 31), ("apr", 4, 30),
        ("may", 5, 31), ("jun", 6, 30), ("jul", 7, 31), ("aug", 8, 31),
        ("sep", 9, 30), ("oct", 10, 31), ("nov", 11, 30), ("dec", 12, 31),
    ])
    log(f"Total entries: {len(by_date)} / expected up to {expected}")
    missing = []
    days_per_month = {1:31, 2:29, 3:31, 4:30, 5:31, 6:30,
                      7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
    for mm in range(1, 13):
        for dd in range(1, days_per_month[mm] + 1):
            k = f"{mm:02d}-{dd:02d}"
            if k not in by_date:
                missing.append(k)
    if missing:
        log(f"Missing days ({len(missing)}): {missing[:20]}{'...' if len(missing) > 20 else ''}")
    else:
        log("Full-year coverage achieved.")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": "https://apostoliki-diakonia.gr/eortologio/",
        "sourceName": "Ἀποστολική Διακονία τῆς Ἐκκλησίας τῆς Ἑλλάδος",
        "fetchedAt": time.strftime("%Y-%m-%d"),
        "entries": dict(sorted(by_date.items())),
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"Wrote {OUT} ({OUT.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
