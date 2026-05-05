"""Post-process glt.goarch.org-fetched akolouthia markdown.

The GOA pages embed:
- Audio links like `[ΤΟ ΑΚΟΥΤΕ](../../music/4079.mp3)` — point to GOA's own
  /music/ path, broken from our site.
- Relative image refs `![...](../../images/...)` — same problem.
- Bullet markers (•) used as metric markers, not list bullets — ugly in Markdown.

This pass strips those artifacts and normalizes whitespace. Idempotent.

Usage:
    python cleanup_akolouthies.py             # all GOA-sourced entries
    python cleanup_akolouthies.py --slug X    # single file
    python cleanup_akolouthies.py --dry-run
"""
from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

from _common import CONTENT_ROOT, log

LITURGICAL_DIR = CONTENT_ROOT / "liturgical"

# Slugs that came from the GOA scraper. Update if seed_akolouthies.py grows.
GOA_SLUGS = {
    # Ωρολόγιον
    "mikron-apodeipnon", "mega-apodeipnon", "mesonyktikon",
    "esperinos", "esperinos-kyriakis", "orthros", "orthros-kyriakis",
    "ora-prote", "ora-trite", "ora-ekte", "ora-enate",
    # Παρακλήσεις / Ακάθιστος
    "paraklesis-mikra", "paraklesis-megale",
    "akathistos-ymnos", "chairetismoi-staseis",
    # Θεῖες Λειτουργίες
    "theia-leitourgia-chrysostomou", "theia-leitourgia-vasileiou",
    "leitourgia-proegiasmenon", "theia-leitourgia-iakovou",
    # Ευχολόγιον
    "mikros-agiasmos", "vaptisma", "stefanoma-gamou",
    "nekrosimos-akolouthia", "mnimosyno-trisagion",
    # Δεσποτικαὶ Ἑορταί
    "megas-agiasmos",
}

# Audio link variants — any [text](relative/path.mp3) pattern.
AUDIO_LINK_RE = re.compile(r"\[[^\]]*\]\([^)]*\.mp3\)")
# Relative-path image references.
REL_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(\.\./[^)]*\)")
# Standalone bullet markers ('• ') that GOA uses as decorative dots.
BULLET_RE = re.compile(r"^\s*•\s+", flags=re.MULTILINE)
# Collapse 3+ blank lines.
EXTRA_BLANK_RE = re.compile(r"\n{3,}")

# ALL-CAPS Greek lines near the top of the body are typically duplicates of
# the title (e.g. "ΑΠΟΔΕΙΠΝΟΝ" / "ΑΚΟΛΟΥΘΙΑ ΤΟΥ ΑΠΟΔΕΙΠΝΟΥ") — strip the
# first 3 such lines so the page doesn't show three stacked titles.
ALL_CAPS_RE = re.compile(r"^[Α-Ω\s]{3,}$")

# Section heading patterns. Lines matching one of these AND being short AND
# not ending with sentence punctuation get prepended with `### ` so they
# render as h3 with the byzantine-purple heading style.
SECTION_HEAD_RE = re.compile(
    r"^("
    r"Ψαλμ[όὸοό][ςσ]\b"
    r"|Δοξολογ[ίι]α\b"
    r"|Ἀπολυτίκ[α-ωᾳᾴᾷ]+\b"
    r"|Καν[ώὼοώ]ν(?!\s+ἐ)"  # "Κανών" but not "Κανὼν ἐλέους"
    r"|ᾨδ[ήὴ]\s+[α-θ][ʹ'`ʹ]?"
    r"|Κάθισμα(τα)?\b"
    r"|Κοντάκι[α-ω]+\b"
    r"|Τροπάρι[α-ω]+\b"
    r"|Στιχηρ[άὰ]\b"
    r"|Συναπτ[ήὴη]\b"
    r"|Ἑωθιν[όὸ]ν\b"
    r"|Ἑξάψαλμος\b"
    r"|Εἱρμ[όὸ]ς\b"
    r"|Μεγαλυνάρι[α-ω]+\b"
    r"|Φῶς\s+ἱλαρ[όὸ]ν\b"
    r"|Σύμβολ[ονν]\s+τῆς\s+Πίστεως\b"
    r"|Πιστεύω(?=\s|$)"  # only the bare word — not "Πιστεύω εἰς..."
    r"|Πάτερ\s+ἡμῶν(?=\s|$|\.\.\.)"
    r"|Ἄξιον\s+ἐστὶ[νν]?(?=\s|$|\.\.\.)"
    r"|Δι'\s+εὐχῶν\b"
    r")"
)


def split_section_headings(line: str) -> str | None:
    """If the line is a recognized short section heading, return the prefixed
    h3 form; otherwise return None.

    Polytonic Greek can encode the same accented letter as either a TONOS
    code point (U+03AF etc., basic Greek block) or an OXIA code point
    (U+1F77 etc., extended Greek). The GOA pages use OXIA forms; the
    regex uses TONOS. We normalize to NFC for matching (which canonicalizes
    OXIA → TONOS) but preserve the original characters in the output.
    """
    stripped = line.strip()
    if len(stripped) > 60:
        return None
    if stripped.endswith((".", ",", "·", ":", ";", "!", "?", "...")):
        return None
    normalized = unicodedata.normalize("NFC", stripped)
    if SECTION_HEAD_RE.match(normalized):
        return f"### {stripped}"
    return None


def clean_body(body: str) -> str:
    body = AUDIO_LINK_RE.sub("", body)
    body = REL_IMAGE_RE.sub("", body)
    body = BULLET_RE.sub("", body)

    # Walk lines: strip top-of-body ALL-CAPS title duplicates, convert
    # recognized section markers into ### h3.
    lines = body.split("\n")
    out: list[str] = []
    seen_real_line = False
    intro_caps_stripped = 0
    for raw in lines:
        s = raw.strip()
        if not s:
            out.append(raw)
            continue
        if not seen_real_line and intro_caps_stripped < 4 and ALL_CAPS_RE.match(s) and len(s) < 60:
            intro_caps_stripped += 1
            continue
        seen_real_line = True
        heading = split_section_headings(raw)
        if heading is not None:
            # Ensure preceding blank line for clean markdown rendering
            if out and out[-1].strip() != "":
                out.append("")
            out.append(heading)
            continue
        out.append(raw)

    body = "\n".join(out)
    body = EXTRA_BLANK_RE.sub("\n\n", body)
    return body.strip() + "\n"


def split_frontmatter(text: str) -> tuple[str, str] | None:
    """Return (frontmatter_inner, body) tuple, or None if not parseable."""
    if not text.startswith("---\n"):
        return None
    rest = text[4:]
    end = rest.find("\n---\n")
    if end == -1:
        return None
    fm = rest[:end + 1]  # include trailing newline
    body = rest[end + 5:]
    return fm, body


def process_file(path: Path, *, dry_run: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    parsed = split_frontmatter(text)
    if parsed is None:
        log(f"  no frontmatter: {path.name}", level="warn")
        return False
    fm, body = parsed

    cleaned = clean_body(body)
    new_text = f"---\n{fm}---\n\n{cleaned}"

    if new_text == text:
        log(f"  unchanged: {path.name}")
        return False

    chars_removed = len(text) - len(new_text)
    log(f"  {'WOULD CLEAN' if dry_run else 'cleaned'} {path.name} (-{chars_removed} chars)",
        level="ok")

    if not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return True


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--slug", help="Process only this slug")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    targets = [args.slug] if args.slug else sorted(GOA_SLUGS)
    log(f"Cleaning {len(targets)} file(s)")

    changed = 0
    for slug in targets:
        path = LITURGICAL_DIR / f"{slug}.md"
        if not path.exists():
            log(f"  missing: {slug}.md", level="warn")
            continue
        if process_file(path, dry_run=args.dry_run):
            changed += 1

    log(f"Done: {changed}/{len(targets)} file(s) {'would change' if args.dry_run else 'cleaned'}",
        level="ok")


if __name__ == "__main__":
    main()
