---
name: manage-news
description: Manage the live Orthodox news aggregator — add or remove RSS sources, adjust the cron schedule, debug missing items, change the widget limit, tune the category classifier. Trigger on "πρόσθεσε νέα πηγή στα νέα", "δεν φαίνονται σωστά τα νέα", "αλλάξω την συχνότητα του news bot", "add an RSS source", "the news widget shows the wrong category", "fix the news pipeline", or any maintenance of the `/news` feeder.
---

# Manage the Orthodox news aggregator

Live news on the home page comes from `scripts/fetch_news.py`, run every
6h by `.github/workflows/news.yml`. Output is `src/data/news.json` (top
30 items). Astro reads the JSON at build time → `<NewsWidget>` on home,
full list at `/news`.

## Architecture

```
[RSS feeds]                 [Python]                [JSON]              [Astro]
romfea / pemptousia    →  fetch_news.py    →   src/data/news.json  →  NewsWidget
dogma / vimaorthodoxias                                                /news pages
                          (every 6h via GitHub Actions cron)
```

## Add a new RSS source

Edit `scripts/fetch_news.py`'s `SOURCES` list:

```python
SOURCES: list[tuple[str, str, str | None]] = [
    ("Πεμπτουσία",      "https://pemptousia.com/feed/",          None),
    ("<Display name>",  "<feed_url>",                            None),
    ...
]
```

Probe the feed first:

```bash
curl -sL -o /tmp/probe.xml -w "%{http_code} %{size_download}\n" -A "Mozilla/5.0" "<feed_url>"
head -c 200 /tmp/probe.xml
```

Confirm 200 status, ~50KB+ payload, response starts with `<?xml ...rss`.
HTML responses (e.g. romfea.gr) need a different scraper — feedparser
won't help.

Re-run locally to verify:

```bash
cd scripts
PYTHONIOENCODING=utf-8 ./venv/Scripts/python.exe fetch_news.py --dry-run
```

Then push without writing — the cron will pick up the new source on
its next run. Or trigger manually:

```bash
gh workflow run news.yml
```

## Adjust cron frequency

Edit `.github/workflows/news.yml`:

```yaml
on:
  schedule:
    - cron: '5 */6 * * *'    # current: every 6 hours at :05
```

Don't go below 1h (rate limits + minimal benefit). 30min minimum if
content velocity demands it.

## Tune category classifier

`fetch_news.py` has `CATEGORY_KEYWORDS` — list of `(label, regex)`
tuples scanned in order against `title + excerpt`. First match wins.
Current labels: liturgy, synod, event, speech, monastic, saints,
general (fallback).

Add a new category:

```python
CATEGORY_KEYWORDS: list[tuple[str, str]] = [
    ...,
    ("pilgrimage", r"προσκυνημα|προσκυνητ"),
    ...
]
```

Then add the i18n label to `src/i18n/ui.ts`:

```ts
'category.pilgrimage': 'Προσκύνημα',  // EL
'category.pilgrimage': 'Pilgrimage',  // EN
```

## Adjust widget item count

In `src/pages/index.astro` (and `/en/index.astro`):

```astro
<NewsWidget limit={5} />
```

Change `limit`. The full `/news` page always shows all 30.

## Debug missing items

```bash
cd scripts
PYTHONIOENCODING=utf-8 ./venv/Scripts/python.exe fetch_news.py --dry-run --limit 50
```

Look for:

- `failed to parse: <bozo_exception>` — feed returned malformed XML or
  redirected somewhere unexpected
- A source returning 0 items — feed URL changed, source down, or
  feedparser can't recognize the format

Each source independently succeeds or fails — one broken feed doesn't
block the others.

## news.json schema

```json
{
  "generated_at": "ISO-8601",
  "count": 30,
  "items": [
    {
      "title": "Headline",
      "url": "https://...",
      "source": "Display name",
      "host": "domain.tld",
      "published": "ISO-8601 or null",
      "excerpt": "First ~280 chars of summary, HTML stripped",
      "category": "liturgy | synod | event | speech | monastic | saints | general"
    }
  ]
}
```

Don't change schema fields without updating `<NewsWidget>` and
`/news/index.astro` simultaneously.

## Don'ts

- Don't add a non-RSS source. The script uses feedparser; HTML scraping
  belongs in a different module.
- Don't disable the cron to "save resources". The whole point is fresh
  content; stale news is a worse UX than no widget.
- Don't hand-edit `src/data/news.json`. The next cron run overwrites
  it. Edit the source list / classifier instead.
- Don't reduce the per-source cap below 25 — some feeds publish 20+
  items per day and a smaller cap loses important news.
