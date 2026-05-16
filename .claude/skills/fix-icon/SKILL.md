---
name: fix-icon
description: Replace or correct the iconUrl/iconAttribution of a specific saint when the auto-fetched Wikimedia Commons icon is wrong, low-quality, Western-style rather than Orthodox, or absent. Trigger on requests like "η εικόνα του Νικολάου είναι λάθος", "βάλε άλλη εικόνα στον <saint>", "fix the icon for <saint>", "βρες καλύτερη εικόνα για...".
---

# Fix or replace a saint's icon

Each saint has optional `iconUrl` and `iconAttribution` fields populated by
`scripts/fetch_icon.py` from Wikipedia/Commons. Sometimes the auto-pick
isn't ideal — a 19th-century Western painting instead of a Byzantine icon,
a low-resolution or poorly cropped file, or no match at all.

## MANDATORY post-step — regenerate the OG share card

Any change to `iconUrl` (Options 1, 2, or any future option) MUST be
followed by re-rendering the saint's 1200×630 OG composite. The existing
`public/og/saints/<slug>.jpg` was built from the OLD icon and will keep
appearing on Facebook/LinkedIn shares until you overwrite it. Invoke the
`regenerate-og-cards` skill — or run the script directly:

```bash
cd scripts && ./venv/Scripts/python.exe _make_og_cards.py --slug <slug> --force
cd ..
```

`--force` is required (the JPG already exists from the previous icon, so
incremental mode would skip it). See `regenerate-og-cards` skill for the
full reasoning.

**Deterministic auto-fire (hook):** Option 2 ("edit the saint markdown
directly") is performed via Claude's Edit tool, which triggers the
`PostToolUse` hook at `.claude/hooks/regen-saint-og-card.py`. The hook
detects `iconUrl:` in the diff and runs the regen automatically with
`--force` — no extra step required. You will see `[regen-og-card] ...`
in the transcript. Option 1 (re-running `fetch_icon.py --update-all`)
writes via Python directly to the filesystem, so the hook can NOT
observe it — the manual regen step above is mandatory in that case.

## Option 1 — try a different Wikipedia title

Edit the saint's `wikipediaTitle` field, then re-fetch:

```bash
cd scripts && ./venv/Scripts/python.exe fetch_icon.py --update-all --force
```

Common title fixes:

- "Spyridon" → "Saint Spyridon" (disambiguation problem)
- A specific name → an article variant the user knows has a good infobox

The fetcher follows interlanguage links, preferring the Greek-Wikipedia
infobox (which usually shows the Orthodox icon) over the English one
(often a Western painting). So updating the input title can route to a
different image.

## Option 2 — pick a Commons file by hand

If `fetch_icon.py` keeps returning the wrong thing:

1. Browse <https://commons.wikimedia.org> and find the desired file. Useful categories:
   - "Category:Orthodox icons"
   - "Category:Icons of <Saint name>"
   - "Category:<Saint name> in icons"
2. Open the file's description page, copy a thumbnail URL of suitable
   size (~600–800px). The pattern is:
   `https://upload.wikimedia.org/wikipedia/commons/thumb/<hash>/<file>/<width>px-<file>`
3. Edit the saint markdown directly:

```yaml
iconUrl: https://upload.wikimedia.org/wikipedia/commons/thumb/.../800px-...jpg
iconAttribution: <Author> · Wikimedia Commons · <License>
```

4. Build and commit:

```bash
npm run build
git add . && git commit -m "fix(icon): replace <saint> icon with <description>" && git push
```

## Quick lookup without modifying anything

```bash
./venv/Scripts/python.exe fetch_icon.py --title "<Wikipedia article title>"
```

This prints filename / URL / artist / license to stdout without writing.
Output also includes a `byzantine?:` line classifying the filename as
`byzantine` / `western` / `uncertain` based on filename keywords.

## Audit: which icons need fixing?

```bash
./venv/Scripts/python.exe fetch_icon.py --audit
```

Pure offline classification — no network. Iterates `saints/*.md`, parses
each `iconUrl` filename, and flags entries as:

- **byzantine**: filename contains icon/sinai/athos/novgorod/rublev/
  fresco/15th-17th century markers
- **western**: filename contains painter names (Raphael, Vasnetsov,
  Repin, Caravaggio, Palma il Vecchio) or oil_on_canvas markers
- **uncertain**: neither pattern matched (the bulk; many are actually fine)
- **missing-iconUrl**: needs a fetch

Use the flagged list to prioritize manual fix-icon passes. False
positives in either direction are common — the audit is a triage tool,
not a verdict.

## Don'ts

- Don't hotlink files outside Wikimedia Commons. We rely on Commons CDN
  and PD/CC licensing. Other hosts' images break the attribution model
  and may break (link rot).
- Don't strip the `?utm_source=...` query parameters Wikimedia adds to
  thumbnail URLs — they're harmless analytics tags. The image still loads.
- Don't set `iconUrl` to point at a low-resolution thumbnail (<300px wide).
  Saint pages render up to 280px wide; smaller sources look pixelated.
- Don't forget to update `iconAttribution` when you change `iconUrl`.
  Stale attribution is worse than no attribution.
