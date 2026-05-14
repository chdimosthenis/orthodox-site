---
name: add-saint
description: Add a new saint to src/content/saints/ with original Greek hagiographic content. Trigger when the user asks to add, create, or write up an Orthodox saint — e.g. "πρόσθεσε τον Άγιο Σάββα", "γράψε για τον Όσιο Πορφύριο", "ο Άγιος Παΐσιος", "add Saint Anthony the Great", expansions of the menologion, or any request to enrich the saints calendar with a new individual entry.
---

# Add a saint

A saint entry lives in `src/content/saints/<slug>.md` and renders at
`/saints/<slug>/`. Two paths to add one — pick by scope:

- **Single ad-hoc entry** → write the file directly (faster).
- **Part of a curated batch** → append to `scripts/calendar_seed.py`'s
  `SAINTS_EL` list and re-run the seeder. Entries written this way are
  easy to regenerate with `--force` if the schema changes.

## Required information

Confirm with the user (or look up):

| Field | Notes |
|---|---|
| `name` | Full Greek form, e.g. "Άγιος Νικόλαος Μύρων της Λυκίας" |
| `feastDay` | MM-DD format. Skip movable feasts (use the `liturgical` collection instead). |
| `category` | `martyr` / `monastic` / `hierarch` / `apostle` / `prophet` / `other` |
| `wikipediaTitle` | English Wikipedia title — used by `fetch_icon.py` to find a Commons icon |
| `tropar`, `kontak` | Optional. Only include traditional centuries-old Byzantine compositions (definitely public domain). Don't include modern published translations. |
| `life` | One-sentence Greek summary (~100 chars max) for cards and the today widget |
| body | 80–120 word original Greek prose. **Do NOT copy from copyrighted sources.** |

## Path A — direct file (single saint)

```
# Pick a slug: transliterated Greek, hyphenated lowercase
# e.g. "Άγιος Σάββας ο Ηγιασμένος" → "agios-savvas-igiasmenos"
```

Write `src/content/saints/<slug>.md`:

```yaml
---
name: Άγιος ...
wikipediaTitle: ...
feastDay: MM-DD
category: ...
tropar: ...   # optional
kontak: ...   # optional
life: One-sentence Greek summary.
language: el
---

Greek body text, 80–120 words, original prose. Use polytonic where
quoting traditional texts; monotonic for modern Greek narrative.
```

**MANDATORY** next step — fetch the icon **and** generate the OG share card
(NEVER commit without both):

```bash
cd scripts && ./venv/Scripts/python.exe fetch_icon.py --update-all
./venv/Scripts/python.exe _make_og_cards.py
cd ..
```

`_make_og_cards.py` reads every saint's `iconUrl` and composes a 1200×630
JPEG card to `public/og/saints/<slug>.jpg` — embedded into a parchment
canvas with the saint name + feast date. Without it, Facebook/LinkedIn
shrink the portrait Wikimedia icon into a brutally-cropped landscape thumb.
The script is incremental (only generates missing files); add `--force` to
re-render an existing card after you edit the saint's frontmatter.

The fetcher iterates every saint, looks up the Greek-Wikipedia infobox
image via `wikipediaTitle`, persists `iconUrl` + `iconAttribution` back
into the frontmatter. Entries without a Wikipedia match are skipped
silently — that's fine, just flag them for later `fix-icon` follow-up.

**Audit step** — after the fetcher runs, grep the new files to verify
icons landed:

```bash
grep -L "iconUrl:" src/content/saints/<new-slug-1>.md src/content/saints/<new-slug-2>.md ...
```

Empty output = all icons resolved. Listed paths = those saints have no
icon yet and either (a) need a tweaked `wikipediaTitle` and re-fetch, or
(b) need manual `iconUrl` via `fix-icon` skill. Either way, do this audit
BEFORE shipping.

Then verify the OG card landed too:

```bash
ls public/og/saints/<new-slug>.jpg
```

Missing = card generation skipped (icon URL probably 404'd at fetch time).
Re-run `_make_og_cards.py --slug <slug> --force` after fixing the icon URL.

Then build + ship:

```bash
npm run build
git add . && git commit -m "feat: add <name> (<feast>)"
git pull --rebase origin main && git push
```

Why mandatory: saint listing cards and the today-widget rely on icons
as the visual cue. Saints without `iconUrl` render as empty boxes,
which makes the page look broken. The user explicitly flagged this on
2026-05-14 after a batch shipped without icons.

## Path B — append to seeder (curated batch)

Edit `scripts/calendar_seed.py`, append a dict to `SAINTS_EL` matching the
existing pattern (slug, frontmatter dict, body string). Then:

```bash
cd scripts && ./venv/Scripts/python.exe calendar_seed.py --force
./venv/Scripts/python.exe fetch_icon.py --update-all
./venv/Scripts/python.exe _make_og_cards.py
cd ..
# audits: every new entry has icon + og card
grep -L "iconUrl:" src/content/saints/<list-of-new-slugs>
ls public/og/saints/<new-slug>.jpg
npm run build
git add . && git commit -m "feat: seed N saints"
git pull --rebase origin main && git push
```

## English version

If the user wants an English counterpart, see the `translate-entry` skill.

## Movable feasts → use the `liturgical` collection instead

Saints with feasts tied to the Paschal cycle (Νεομάρτυρες Χίου, Σαββατο
τῆς Α' Ἑβδομάδος, Κυριακή τῶν Ἁγίων Πατέρων, etc.) cannot be added here
— the schema enforces `feastDay: MM-DD` and Zod will reject anything
else. Add them as `liturgical` entries with a written note about how
the date is computed relative to Pascha.

## Polytonic vs monotonic for the body

The existing corpus is mixed. Match the entry's register:
- **Hagiographies from Byzantine sources** → polytonic (Ἅγιος, Ὀρθόδοξος…).
- **Modern Greek narrative** → monotonic (Άγιος, Ορθόδοξος…).

The `name` frontmatter field is conventionally monotonic across the
corpus. Use polytonic only when the source you're paraphrasing is
itself polytonic.

## Body length

80–120 words for the body. Saint listing cards excerpt the first
~150 chars; longer bodies are fine but the first paragraph carries
most of the SEO and card weight.

## Don'ts

- Don't make up Wikipedia titles that don't exist — verify or omit the
  field (icons can be added later via `fix-icon`).
- Don't include copyrighted modern Greek translations of patristic texts.
- Don't set `iconUrl` manually as the first attempt — let `fetch_icon.py`
  resolve it from `wikipediaTitle`. Use the `fix-icon` skill if a specific
  Commons file is wanted.
- Don't commit without running `npm run build` first — schema validation
  errors only surface there.
- Don't commit without running `fetch_icon.py --update-all` first —
  the audit step above catches missing icons before they ship.
- Don't commit without running `_make_og_cards.py` first — saints without
  an OG card get badly cropped on Facebook/LinkedIn shares (the raw
  Wikimedia icon is portrait, the FB/LI card slot is 1.91:1 landscape).
- Don't write the body as a transcription of an external hagiography —
  paraphrase in original Greek prose to avoid copyright issues.
