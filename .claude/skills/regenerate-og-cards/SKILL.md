---
name: regenerate-og-cards
description: Regenerate the 1200×630 OG share-card composite for one or more saints by invoking `scripts/_make_og_cards.py`. **Trigger automatically (proactively) whenever a saint entry is added or modified** — i.e. on every `add-saint`, every `fix-icon`, every batch run of `fetch_icon.py`, every edit to a saint's `name` / `feastDay` / `iconUrl` frontmatter, and every `seed-batch` / `bulk-seed-and-publish` close. ALSO fires on explicit phrases — "regenerate og cards", "rebuild saint cards", "refresh linkedin thumbnails", "ξαναφτιάξε τις κάρτες", "ξανατρέξε τα og", "καθε φορα που ανεβαινει αγιος", "κάθε φορά που μπαίνει φωτογραφία". Encodes per-slug targeting (avoid re-rendering all 463 cards when one changes), the `--force` flag (needed when re-rendering existing slugs after frontmatter edits), and the audit step (`ls public/og/saints/<slug>.jpg`) that confirms the file landed.
---

# Regenerate per-saint OG share cards

The composite cards live under `public/og/saints/<slug>.jpg`. They are
emitted by `scripts/_make_og_cards.py` from each saint's frontmatter:
`name` + `feastDay` + `iconUrl`. Without them, Facebook/LinkedIn crop
the portrait Wikimedia icon into the 1.91:1 landscape card slot and the
share looks broken.

## When this skill fires

**Automatically (proactive):**

| Upstream event | Skill that just ran | This skill's job |
|---|---|---|
| New saint added | `add-saint` | Generate the new slug's card |
| Saint's icon URL fixed/replaced | `fix-icon` | Re-render that slug with `--force` |
| Bulk seeder run | `seed-batch` / `bulk-seed-and-publish` | Sweep — generate any missing |
| `fetch_icon.py --update-all` adds icons to N saints | `add-saint` (batch path) | Sweep — generate any missing |
| Saint frontmatter edited (`name` / `feastDay`) | (manual edit) | Re-render that slug with `--force` |

**Manually (explicit invocation):** when the user says any of the
trigger phrases in the description above, or after a brand-design pass
that touches the card template inside `_make_og_cards.py` itself
(re-render everything with `--force`).

## The mechanical step

From `C:\Users\dimos\Documents\orthodox-site\`:

**Single new saint** (or after `fix-icon`):

```bash
cd scripts && ./venv/Scripts/python.exe _make_og_cards.py --slug <slug> --force
cd ..
```

`--force` is REQUIRED when re-rendering an existing slug — without it the
script sees the existing `public/og/saints/<slug>.jpg` and skips. After
`fix-icon` or any frontmatter edit, the file exists but its content is
stale; `--force` overrides the existence check.

**Batch (multiple new saints after seed)**:

```bash
cd scripts && ./venv/Scripts/python.exe _make_og_cards.py
cd ..
```

Incremental by default — only generates missing files. Fast (cards that
already exist are skipped on the existence check before any Wikimedia
fetch happens).

**Full sweep (after a template change in `_make_og_cards.py` itself)**:

```bash
cd scripts && ./venv/Scripts/python.exe _make_og_cards.py --force
cd ..
```

Re-renders all 463+ cards. Takes ~5-10 minutes due to the 0.5s shared
Wikimedia rate limiter. Plan accordingly.

## Audit step (always)

After running, confirm the file landed:

```bash
ls public/og/saints/<slug>.jpg
```

Missing file = icon URL probably 404'd or rate-limited. Re-run with
`--force` and watch stderr — `[SKIP]` lines name the failing slug.

For batch runs:

```bash
ls public/og/saints/ | wc -l
```

Compare against the saint count: `find src/content/saints -name "*.md" | wc -l`.
Saints without `iconUrl` are skipped silently (intentional — they have
no icon to composite, so they fall back to the brand `og-default.png`).
The two counts differ by exactly the number of icon-less saints.

## Why slug targeting matters

Without `--slug`, re-rendering after a single edit triggers Wikimedia
fetches for every saint whose card is missing (the rate-limited path).
Even when nothing else changed, the script doesn't know that — its only
state is the file system.

For a single saint edit, always pass `--slug`. For a known set of new
slugs from a batch, pass them one at a time or let the incremental
mode handle it (faster, since cached cards are skipped before the
Wikimedia GET).

## Why `--force` is needed after `fix-icon`

The default incremental check is: "does `public/og/saints/<slug>.jpg`
exist?" If yes, skip. After `fix-icon` replaces the `iconUrl`, the
output JPG still exists from the previous (wrong) icon — but its
content is now stale. `--force` overrides the existence check and
re-fetches + re-renders.

## Why `_make_og_default.py` is separate

Brand-default OG image regeneration (`public/og-default.png`) lives in
`scripts/_make_og_default.py`, NOT in this skill. The brand default is
the fallback for entries without their own OG image (articles without
`image:`, erminia, fathers, etc.) and is regenerated rarely — only on
brand-design changes.

This skill is exclusively about per-saint composites.

## Don'ts

- **Don't** skip the regeneration step on `fix-icon`. The OG card will
  keep serving the OLD icon's composite even after the saint page
  itself shows the new one. Facebook/LinkedIn will scrape stale shares
  until a cachebust forces re-fetch.
- **Don't** run a full `--force` sweep "just to be safe" — it re-fetches
  every Wikimedia icon and burns ~5-10 minutes of rate-limited time. Use
  `--slug <slug>` for targeted re-renders.
- **Don't** commit without confirming the JPG landed via `ls`. Missing
  files mean a silent skip, which means the share will fall back to the
  brand default — losing the saint's visual identity in the preview.
- **Don't** try to extend this to articles. Articles use the
  `image:` frontmatter field directly as og:image, already at 1200×630
  per `add-article` skill guidance. No composite step is needed (and
  none would help — article hero images are designer-prepared, not
  auto-fetched from a third-party source).
