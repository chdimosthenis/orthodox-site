"""Generate per-saint OG composite cards (1200x630 PNG) for social sharing.

Why: saint pages emit `iconUrl` (Wikimedia thumb) as og:image. Those are
portrait orientation, so Facebook/LinkedIn crop them brutally to fit the
1.91:1 landscape card slot. The composite card embeds the icon at proper
aspect inside a branded 1200x630 canvas, so shares look intentional.

Output: public/og/saints/<slug>.jpg — referenced by /saints/<slug>/ pages.
JPEG at quality 85 keeps each card ~60-90KB (vs ~340KB as PNG), so 463
saints fit in ~30MB of static assets instead of ~150MB.

Usage:
    cd scripts && ./venv/Scripts/python.exe _make_og_cards.py
    # incremental — only renders missing files

    ./venv/Scripts/python.exe _make_og_cards.py --force
    # re-render everything

    ./venv/Scripts/python.exe _make_og_cards.py --slug agios-georgios
    # one specific saint

    ./venv/Scripts/python.exe _make_og_cards.py --slug agios-georgios --force
    # force re-render one saint (useful after editing frontmatter)
"""
from __future__ import annotations
import argparse
import re
import sys
import threading
import time
from io import BytesIO
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from PIL import Image, ImageDraw, ImageFont, ImageFile

# Some Wikimedia thumbs arrive with a missing terminator byte; tolerate it
# rather than failing the whole card.
ImageFile.LOAD_TRUNCATED_IMAGES = True

ROOT = Path(__file__).resolve().parent.parent
SAINTS_DIR = ROOT / "src" / "content" / "saints"
OUT_DIR = ROOT / "public" / "og" / "saints"

W, H = 1200, 630
PARCHMENT_TOP = (250, 246, 237)
PARCHMENT_BOT = (240, 233, 212)
GOLD = (176, 141, 87)
BURGUNDY = (107, 27, 44)
INK = (26, 20, 16)
MUTED = (110, 98, 88)

MONTHS_GR = [
    "Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου",
    "Μαΐου", "Ιουνίου", "Ιουλίου", "Αυγούστου",
    "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου", "Δεκεμβρίου",
]

UA = "orthodoxoskomvos/1.0 (+https://orthodoxoskomvos.gr; admin@orthodoxoskomvos.gr)"

# Wikimedia rate-limits aggressively. A shared inter-request delay keeps us
# well under their bot-traffic threshold even with multiple workers.
_RATE_LOCK = threading.Lock()
_LAST_FETCH = [0.0]
RATE_DELAY = 0.5  # seconds between consecutive Wikimedia fetches


def parse_frontmatter(path: Path) -> dict[str, str]:
    txt = path.read_text(encoding="utf-8")
    m = re.match(r"^---\r?\n(.*?)\r?\n---", txt, re.DOTALL)
    if not m:
        return {}
    fm: dict[str, str] = {}
    for line in m.group(1).splitlines():
        m2 = re.match(r"^([a-zA-Z_]+):\s*(.+?)\s*$", line)
        if m2:
            fm[m2.group(1)] = m2.group(2).strip().strip('"\'')
    return fm


def find_font(candidates: list[str], size: int):
    for name in candidates:
        try:
            return ImageFont.truetype(name, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


def gradient_fill() -> Image.Image:
    img = Image.new("RGB", (W, H), PARCHMENT_TOP)
    px = img.load()
    assert px is not None
    for y in range(H):
        t = y / (H - 1)
        for x in range(W):
            tx = x / (W - 1)
            mix = (t + tx) / 2
            px[x, y] = (
                round(PARCHMENT_TOP[0] * (1 - mix) + PARCHMENT_BOT[0] * mix),
                round(PARCHMENT_TOP[1] * (1 - mix) + PARCHMENT_BOT[1] * mix),
                round(PARCHMENT_TOP[2] * (1 - mix) + PARCHMENT_BOT[2] * mix),
            )
    return img


# Pre-compute the gradient once — it's the same for every card and
# costs ~0.5s per render to recompute. Saves minutes across 463 saints.
_BASE_BG: Image.Image | None = None


def base_bg() -> Image.Image:
    global _BASE_BG
    if _BASE_BG is None:
        _BASE_BG = gradient_fill()
    return _BASE_BG.copy()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        candidate = (cur + " " + w).strip()
        bbox = draw.textbbox((0, 0), candidate, font=font)
        if bbox[2] - bbox[0] <= max_width:
            cur = candidate
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def shrink_to_fit(draw: ImageDraw.ImageDraw, text: str, font_candidates: list[str],
                  sizes: list[int], max_width: int, max_lines: int) -> tuple[list[str], int]:
    """Try font sizes from largest to smallest; return wrapped lines + final size."""
    for sz in sizes:
        font = find_font(font_candidates, sz)
        lines = wrap_text(draw, text, font, max_width)
        if len(lines) <= max_lines:
            return lines, sz
    # Fallback: use smallest size anyway, truncate lines
    sz = sizes[-1]
    font = find_font(font_candidates, sz)
    lines = wrap_text(draw, text, font, max_width)[:max_lines]
    return lines, sz


def _rate_limited_get(url: str, timeout: int = 25):
    with _RATE_LOCK:
        wait = RATE_DELAY - (time.monotonic() - _LAST_FETCH[0])
        if wait > 0:
            time.sleep(wait)
        _LAST_FETCH[0] = time.monotonic()
    return requests.get(url, timeout=timeout, headers={"User-Agent": UA})


def fetch_icon(url: str, retries: int = 3) -> Image.Image:
    last_exc: Exception | None = None
    for attempt in range(retries + 1):
        try:
            r = _rate_limited_get(url)
            if r.status_code == 429:
                # Honor Retry-After if present, else escalating backoff
                ra = r.headers.get("Retry-After")
                delay = float(ra) if ra and ra.isdigit() else (2 ** attempt) * 2
                time.sleep(min(delay, 30))
                continue
            r.raise_for_status()
            img = Image.open(BytesIO(r.content))
            img.load()  # force decode now so truncation surfaces here
            return img.convert("RGBA")
        except Exception as e:
            last_exc = e
            time.sleep(1 + attempt)
            continue
    assert last_exc is not None
    raise last_exc


def format_feast(feast_day: str) -> str:
    if not feast_day or len(feast_day) != 5 or feast_day[2] != "-":
        return ""
    try:
        m_str, d_str = feast_day.split("-")
        m = int(m_str)
        d = int(d_str)
        if not (1 <= m <= 12):
            return ""
        return f"Μνήμη: {d} {MONTHS_GR[m - 1]}"
    except (ValueError, IndexError):
        return ""


def make_card(slug: str, name: str, feast_day: str, icon_url: str) -> bool:
    out = OUT_DIR / f"{slug}.jpg"
    try:
        icon = fetch_icon(icon_url)
    except Exception as e:
        print(f"  [SKIP] {slug}: icon fetch failed: {e}", file=sys.stderr)
        return False

    img = base_bg()
    drw = ImageDraw.Draw(img)

    # Outer ornament border
    drw.rectangle([40, 40, W - 40, H - 40], outline=GOLD, width=2)

    # Icon placement — fit within 380x480 box anchored at (70, 75)
    box_x, box_y, box_w, box_h = 70, 75, 380, 480
    icon.thumbnail((box_w, box_h), Image.LANCZOS)
    ix = box_x + (box_w - icon.width) // 2
    iy = box_y + (box_h - icon.height) // 2

    # Subtle drop-shadow rectangle behind icon
    drw.rectangle(
        [ix + 5, iy + 5, ix + icon.width + 5, iy + icon.height + 5],
        fill=(0, 0, 0, 30),
    )
    img.paste(icon, (ix, iy), icon)
    # Gold frame
    drw.rectangle(
        [ix - 4, iy - 4, ix + icon.width + 4, iy + icon.height + 4],
        outline=GOLD, width=3,
    )

    # Text area on the right
    tx = 490
    text_w = W - tx - 70  # ~640px
    # Polytonic Greek (Ἅ, Ἰ, ὁ, Ἀ) is in the Greek Extended Unicode block.
    # Georgia covers only basic Greek (Α–Ω, α–ω) — saint names with
    # breathing marks render as tofu. Palatino Linotype / Cambria / Times
    # all carry Greek Extended on Windows and are tried first.
    fonts_serif_b = ["palab.ttf", "cambriab.ttf", "timesbd.ttf",
                     "georgiab.ttf", "DejaVuSerif-Bold.ttf"]
    fonts_serif = ["pala.ttf", "cambria.ttc", "times.ttf",
                   "georgia.ttf", "DejaVuSerif.ttf"]

    # Saint name — shrink to fit 3 lines max
    title_lines, title_sz = shrink_to_fit(
        drw, name, fonts_serif_b,
        sizes=[58, 52, 46, 40, 36, 32],
        max_width=text_w, max_lines=3,
    )
    font_title = find_font(fonts_serif_b, title_sz)
    line_h = int(title_sz * 1.25)
    total_h = len(title_lines) * line_h
    feast_str = format_feast(feast_day)
    extra = 60 if feast_str else 0
    block_h = total_h + extra
    ty = (H - block_h) // 2 - 20
    for line in title_lines:
        bbox = drw.textbbox((0, 0), line, font=font_title)
        drw.text((tx - bbox[0], ty), line, fill=INK, font=font_title)
        ty += line_h

    # Feast date
    if feast_str:
        font_date = find_font(fonts_serif, 30)
        bbox = drw.textbbox((0, 0), feast_str, font=font_date)
        drw.text((tx - bbox[0], ty + 20), feast_str, fill=BURGUNDY, font=font_date)

    # Brand mark bottom-center
    brand = "orthodoxoskomvos.gr"
    font_brand = find_font(fonts_serif, 24)
    bbox = drw.textbbox((0, 0), brand, font=font_brand)
    bw = bbox[2] - bbox[0]
    drw.text(
        ((W - bw) / 2 - bbox[0], H - 75),
        brand, fill=MUTED, font=font_brand,
    )

    # JPEG can't carry alpha; the composition is on an opaque background
    # so .convert("RGB") just drops the unused alpha channel.
    img.convert("RGB").save(out, "JPEG", quality=85, optimize=True, progressive=True)
    return True


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--force", action="store_true",
                   help="re-render cards even if output exists")
    p.add_argument("--slug",
                   help="only generate this single slug")
    p.add_argument("--workers", type=int, default=6,
                   help="parallel fetch workers (default 6)")
    args = p.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Build the work queue first
    jobs: list[tuple[str, str, str, str]] = []  # (slug, name, feast, icon)
    for md in sorted(SAINTS_DIR.glob("*.md")):
        slug = md.stem
        if args.slug and slug != args.slug:
            continue
        fm = parse_frontmatter(md)
        icon = fm.get("iconUrl", "").strip()
        if not icon:
            continue
        name = fm.get("name", slug).strip()
        feast = fm.get("feastDay", "").strip()
        out = OUT_DIR / f"{slug}.jpg"
        if out.exists() and not args.force:
            continue
        jobs.append((slug, name, feast, icon))

    if not jobs:
        print("Nothing to do — all cards already exist (use --force to rebuild).")
        return 0

    print(f"Generating {len(jobs)} cards with {args.workers} workers...")
    made = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futures = {ex.submit(make_card, *job): job[0] for job in jobs}
        for f in as_completed(futures):
            ok = f.result()
            if ok:
                made += 1
                if made % 25 == 0:
                    print(f"  ...{made}/{len(jobs)}")
            else:
                failed += 1

    print(f"\nDone: {made} cards generated, {failed} failed.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
