# SEO guidelines — Ὀρθόδοξος Κόμβος

The site is engineered for organic discoverability from day one. This
document is the single source of truth for what's already in place,
what to verify after launch, and what to monitor going forward.

## What's built into every page

The `BaseLayout` automatically emits all of the following on every page:

### Title & description
- `<title>` is `${page-title} — ${siteTitle}`, with the home page collapsed
  to just the brand. Each route has a unique title.
- `<meta name="description">` falls back to `site.tagline` when not set
  per page; richer content pages override it with their own description.
  Aim 150-160 chars per page.

### Crawler directives
- `<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">` — lets Google use full-length snippets and large image previews in SERPs.
- `noindex` opt-in: `BaseLayout` accepts a `noindex={true}` prop. Already
  set on `/search` (search-result pages should not be indexed).
- `robots.txt` allows GPTBot, Google-Extended, ClaudeBot — embracing AI
  indexing of the public-domain content.

### Canonical URL
- `<link rel="canonical">` on every page, derived from `Astro.url.pathname`
  + the site's `site:` config. Auto-updates with domain change.

### Open Graph + Twitter
- `og:title`, `og:description`, `og:type` (`website`), `og:url`,
  `og:image`, `og:image:width=1200`, `og:image:height=630`, `og:locale=el_GR`
- `twitter:card=summary_large_image`, `twitter:image`
- Default OG image: `/og-default.png` (1200×630, brand colors, generated
  via `scripts/_make_og_default.py`)
- Per-saint pages override `ogImage` with the saint's icon URL —
  shares show the icon as the thumbnail.

### Sitemap
- `@astrojs/sitemap` integration auto-generates `sitemap-index.xml` at
  build time. All static + dynamic routes are included automatically.
- `robots.txt` has the `Sitemap:` line pointing to the production URL.

### RSS feed
- `<link rel="alternate" type="application/rss+xml">` exposes `/rss.xml`
  in the head — feed readers and crawlers auto-discover it.

### Structured data (JSON-LD)
- **Every page**: `WebSite` schema with `SearchAction` (Google sitelinks
  search box eligibility).
- **Hub pages**: `BreadcrumbList` (rich breadcrumbs in SERPs). Wired
  on `/didaskalia`, `/prosopa`, `/latreia`, `/bible`.
- **Articles** (`/articles/[slug]`, `/bible/erminies/[slug]`): `Article`
  schema with headline, datePublished, author, description, license.
- **Saints** (`/saints/[slug]`): `Person` schema with `honorificPrefix`
  ("Άγιος"), description, language.
- **Fathers** (`/fathers/[slug]`): `Person` + `hasOccupation` =
  "Πατὴρ τῆς Ἐκκλησίας".
- **Bible books** (`/bible/[book]`): `Book` schema with isPartOf =
  "Ἡ Καινὴ Διαθήκη".

## Static-site advantages

The site is fully pre-rendered HTML (no JavaScript-rendered content).
This is the **best possible architecture for SEO** — crawlers see the
final markup immediately, no rendering budget consumed, no race
conditions.

- 374 pages prerendered
- All search-engine-discoverable content available without JS
- Pagefind search index works without server roundtrips

## Performance

Cloudflare Pages serves the static HTML from CDN edges globally. Expect:
- LCP (Largest Contentful Paint): < 1.5s
- Lighthouse Performance: 95+ (verify after launch with
  https://pagespeed.web.dev/)
- Core Web Vitals: all green

## Mobile

- Responsive media queries at ≤720px and ≤480px breakpoints
- Tables become horizontally-scrollable on narrow widths (eortologio,
  monasteries)
- Headings and paddings scale down for phone viewing
- `<meta name="viewport" content="width=device-width, initial-scale=1">`

## After domain goes live — one-time SEO setup

### 1. Submit sitemap to search engines

**Google Search Console**:
1. https://search.google.com/search-console → Add property
2. URL prefix → `https://orthodoxoskomvos.gr`
3. Verify via Cloudflare DNS TXT record (one-click if DNS is on Cloudflare)
4. Sitemaps panel → Add → `https://orthodoxoskomvos.gr/sitemap-index.xml`
5. International Targeting → Country → Greece (since content is Greek-only)

**Bing Webmaster Tools**:
1. https://www.bing.com/webmasters → Add site
2. Same flow. Bing also feeds DuckDuckGo, Ecosia, Yandex.

### 2. Test rich-snippet eligibility

Use Google's Rich Results Test on representative pages:

```
https://search.google.com/test/rich-results?url=https://orthodoxoskomvos.gr/saints/agios-nektarios-pentapoleos
https://search.google.com/test/rich-results?url=https://orthodoxoskomvos.gr/fathers/grigorios-palamas
https://search.google.com/test/rich-results?url=https://orthodoxoskomvos.gr/articles/proseyhi-iisou
https://search.google.com/test/rich-results?url=https://orthodoxoskomvos.gr/bible/kata-ioannin
https://search.google.com/test/rich-results?url=https://orthodoxoskomvos.gr/didaskalia
```

You should see:
- Person schema (saints, fathers)
- Article schema (articles, erminies)
- Book schema (bible)
- BreadcrumbList (hub pages)
- WebSite + SearchAction (homepage)

### 3. Cloudflare Web Analytics (optional, free, privacy-friendly)

Pages dashboard → Analytics → Web Analytics → enable. No cookies,
GDPR-compliant, gives you basic traffic stats without third-party
tracking pixel.

## Monitoring (after first month live)

Watch in Search Console:
- **Coverage report**: how many pages are indexed (target: all 374)
- **Core Web Vitals**: should stay green
- **Search Performance**: which queries bring traffic
- **Backlinks**: who's linking to you

Report tab to watch:
- **Pages > Indexing**: any "Discovered — currently not indexed" issues
- **Page experience**: should be Good/Excellent

## Realistic timeline

- **Day 1-3 after domain goes live**: Cloudflare propagation + SSL.
  Search Console verification.
- **Week 1-2**: Google starts indexing. Most pages indexed by week 3.
- **Month 3-6**: First page-1 rankings for niche Greek queries
  ("Ἅγιος Νεκτάριος βίος", "Παραβολὴ Καλοῦ Σαμαρείτη ἑρμηνεία").
- **Month 6-12**: Significant organic traffic if content stays fresh.

## Optional improvements (already in code, can be enabled later)

- **News auto-cron**: `news.yml` runs every 6h and archives by date.
  Already producing fresh-content signal to Google.
- **Author entity**: could add `Person` schema for "Σύνταξη" — skip
  unless real author identity is set up.
- **Speakable schema**: for voice-assistant answers — relevant if you
  want Greek Orthodox content surfaced via Alexa/Google Assistant.

## What NOT to do

- **Don't** install Google Tag Manager / GA4. Cloudflare's analytics is
  enough; GTM hurts page speed.
- **Don't** buy backlinks. Will trigger manual penalties.
- **Don't** add hreflang tags. The site is Greek-only; hreflang only
  matters for multi-locale sites.
- **Don't** submit individual URLs to Google. The sitemap handles
  everything; manual submission is rate-limited and unnecessary.
- **Don't** install SEO plugins. Astro's built-in capabilities + the
  schema markup we emit are already at "professional SEO consultant"
  level — there's no plugin that adds anything we don't already have.

## Code references

| What | Where |
|---|---|
| All meta tags + JSON-LD orchestration | `src/layouts/BaseLayout.astro` |
| Article schema | `src/pages/articles/[...slug].astro` |
| Person schema (saints) | `src/pages/saints/[...slug].astro` |
| Person schema (fathers) | `src/pages/fathers/[...slug].astro` |
| Book schema | `src/pages/bible/[...slug].astro` |
| BreadcrumbList prop wiring | `src/pages/didaskalia.astro` (model example) |
| Sitemap config | `astro.config.mjs` (`sitemap()` integration) |
| robots.txt | `public/robots.txt` |
| OG image generator | `scripts/_make_og_default.py` |

To add breadcrumbs to any page, pass:
```astro
<BaseLayout breadcrumbs={[
  { name: 'Λατρεία', url: '/latreia' },
  { name: 'Μοναστήρια', url: '/monasteries' }
]}>
```
The home page is auto-prefixed.

To noindex a page (e.g. a draft):
```astro
<BaseLayout noindex={true}>
```
