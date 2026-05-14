---
name: add-article
description: Add a new article (essay, patristic text, theological piece, devotional reflection) to the articles content collection. Trigger on "πρόσθεσε άρθρο", "γράψε ένα κείμενο για...", "δημοσίευσε αυτό το κείμενο", "add an article", or requests to publish a piece of long-form writing on the site.
---

# Add an article

Articles live in `src/content/articles/<slug>.md`, rendered at
`/articles/<slug>/`. Schema requires: title, description, pubDate, author,
language. Optional: sourceUrl, license, tags, draft, **updatedDate**, **image**.

- `updatedDate` (ISO date) — set when you genuinely revise an article. Emits
  `dateModified` in the Article JSON-LD and `article:modified_time` in
  Open Graph. A freshness signal for Google + a richer social-share preview.
- `image` (root-relative path under `public/`, e.g. `/articles/hero-foo.jpg`) —
  per-article hero image used as og:image. Falls back to the brand
  `og-default.png` when absent. Adding this on your most-shared articles
  makes each FB/LinkedIn/X preview visually unique → higher click-through.

## Two paths

**Path A — original content**: write directly. License = `original`.

**Path B — imported from a public source**: use one of the fetchers in
`scripts/`. License is set by the fetcher (CCEL → public-domain;
OrthodoxWiki → CC-BY-SA; Myriobiblos → public-domain pending manual
verification).

## Path A — original article

Pick a slug (transliterated, hyphenated, lowercase). Write the file:

```yaml
---
title: "Title in the article's language"
description: "1–2 sentence summary for cards and SEO meta description."
pubDate: 2026-MM-DD
# updatedDate: 2026-MM-DD       # optional — only when genuinely revised
author: "Author name (or 'Σύνταξη' for editorial pieces)"
language: el
license: original
tags: ["tag1", "tag2"]
# image: /articles/hero-foo.jpg  # optional — per-article og:image override
---

Body in Markdown. Use:
- ## headings for sections (NEVER a second H1 — the slug page renders
  the title as H1 itself).
- > blockquotes (with `<blockquote lang="grc">` if quoting polytonic
  patristic Greek)
- Inline citations for any external work referenced
```

**SEO writing notes:**
- Match the H1 to a real Greek search query the article answers. The
  article slug page emits `entry.data.title` as H1 already; keep it
  semantic (question form like "Πῶς…", "Τί εἶναι…", "Γιατί…" outperforms
  generic noun titles for long-tail search intent).
- Aim for 400–800 words. Shorter pieces don't rank; longer ones get
  scroll-fatigue from mobile readers.
- Use 4–6 H2 sections. Greek SERPs favor structured content with TOC-like
  skim affordances.
- Tags drive the on-site Σχετικά (related articles) block via shared-tag
  overlap. Pick 3–4 tags that cluster with peer articles, not abstract
  metadata.

Ship:

```bash
npm run build
git add . && git commit -m "feat: add article <title>"
git pull --rebase origin main && git push
```

## Path B — fetched

See the `fetch-content` skill. After the fetcher writes the file,
**always review the output** before committing — boilerplate from the
source page (navigation, footnote markers, "edit" links) sometimes leaks
through despite the cleaning step.

## Bilingual

The site has separate Greek and English views. To publish an article in
both languages, write two files with different `language` values. Use
either the same slug (filtered by language at render time) or
language-suffixed slugs:

- `proseyhi-iisou.md` (`language: el`)
- `proseyhi-iisou-en.md` (`language: en`)

Greek view: `/articles/proseyhi-iisou/`. English view: `/en/articles/proseyhi-iisou-en/`.

## Don'ts

- Don't omit `pubDate` — RSS feed and listings sort by it.
- Don't commit fetched articles without reviewing the body for source
  artifacts.
- Don't lose `sourceUrl` + `license` on imported content — both render
  in the attribution box at the bottom of the article page.
- Don't set `license: original` on a derivative translation. Use
  CC-BY-SA if from a CC-BY-SA source, or public-domain if from PD.
