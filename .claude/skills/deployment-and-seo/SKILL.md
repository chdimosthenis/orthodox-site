---
name: deployment-and-seo
description: Post-launch operational state of orthodoxoskomvos.gr — what's actually deployed where, what was changed at the Cloudflare zone, how Search Console + Bing are wired, and the JSON-LD / related-articles enhancements added on 2026-05-14. Read this FIRST when the user asks about deployment, hosting, SEO, search indexation, sitemap, Cloudflare settings, Bing / GSC, or "why is X showing up in search like that". Supersedes (but does not replace) DEPLOY.md and SEO.md, which describe the pre-launch architecture.
---

# Deployment + SEO — post-launch operational state

## Live status (as of 2026-05-14)

- Production URL: `https://orthodoxoskomvos.gr`
- Worker fallback URL: `https://orthodoxoskomvos.dimos-chatzinikolaou.workers.dev`
- GitHub repo: `chdimosthenis/orthodox-site`, branch `main`
- Hosting: Cloudflare **Workers + Static Assets** (the unified Pages/Workers path; that's why the fallback is `*.workers.dev`, not `*.pages.dev`)
- Auto-deploy: every push to `main` rebuilds in ~1-2 min
- Build command: `astro build && pagefind --site dist`
- Build output: 424 pages, Pagefind indexes ~28,576 words across 1 language (el)
- Node version: pinned to **22.12.0** via `.nvmrc` (required — Cloudflare's default is older and breaks the Astro 6 build)

## Domain history — the actual path that worked

The domain was on **Papaki** (Greek registrar), not on Cloudflare, at the start of this deployment. Adding it to Cloudflare and changing nameservers was a required prerequisite. The 4-step playbook that worked:

1. Cloudflare dashboard → **Add a site** → enter `orthodoxoskomvos.gr` → Free plan
2. Cloudflare returns 2 nameservers (e.g. `xxx.ns.cloudflare.com`)
3. Papaki dashboard (`my.papaki.gr` → Τα Domain μου → Διαχείριση) → change nameservers to the Cloudflare ones
4. Wait for zone status to become **Active** (≤ 24h for .gr, typically much faster), then attach the custom domain to the Worker in dashboard → Workers & Pages → orthodox-site → Custom Domains

If Cloudflare's UI says *"Only domains active on your Cloudflare account can be added"* when attaching a custom domain, the zone is not Active yet — wait, then retry.

## Cloudflare zone settings (do once, done as of 2026-05-14)

| Path | Setting | Value |
|---|---|---|
| SSL/TLS → Overview | Encryption mode | **Full** (not Flexible) |
| SSL/TLS → Edge Certificates | Always Use HTTPS | ON |
| SSL/TLS → Edge Certificates | Automatic HTTPS Rewrites | ON |
| SSL/TLS → Edge Certificates | Min TLS Version | 1.2 |
| SSL/TLS → Edge Certificates | HSTS | Enabled, max-age 6 months, include subdomains, preload OFF |
| Speed → Optimization → Content | Brotli | ON |
| Speed → Optimization → Content | Early Hints | ON |
| Caching → Configuration | Browser Cache TTL | "Respect existing headers" |
| Rules → Page Rules / Cache Rules | Static assets (`*.css *.js *.png *.svg *.woff2`) | Edge TTL ≥ 1 month |
| Cache → Configuration | IndexNow | ON (auto-pings Bing/Yandex on every change) |

`www` vs apex: decide canonical, redirect the other with a Bulk Redirect or Page Rule. (Currently the custom domain is on the apex only.)

## Robots.txt — Cloudflare may rewrite yours

⚠️ The user's `public/robots.txt` explicitly **allows** GPTBot / Google-Extended / ClaudeBot. But Cloudflare's zone-level **"Block AI bots" / "AI Audit"** feature can inject a Content-Signal framework on top that *disallows* those exact bots.

What you'll see if Cloudflare is overriding: fetch `https://orthodoxoskomvos.gr/robots.txt` and look for a `Content-Signal: search=yes,ai-train=no` block + `User-agent: ClaudeBot \n Disallow: /` lines that aren't in the repo's `public/robots.txt`.

Resolution: in zone dashboard → **Security → Bots → Configure** → toggle OFF "Block AI bots" / "AI Labyrinth" / "AI Audit" (depending on which one is active). The user's repo policy is to allow AI crawlers; Cloudflare's default policy is to block them.

Also confirm **Bot Fight Mode** is OFF — it can rate-limit Googlebot during traffic spikes if not properly verified.

## Search Console + Bing — current wiring

- **Google Search Console**: verified for `orthodoxoskomvos.gr` (Domain property via DNS TXT). Sitemap `https://orthodoxoskomvos.gr/sitemap-index.xml` submitted. Watch the Pages / Sitemaps reports.
- **Bing Webmaster Tools**: imported from GSC via the **left-panel "Import your sites from GSC"** button. The right-panel "XML File" verification method returns *"Error: Unexpected error occurred"* in their UI — known broken, use Import-from-GSC instead. Zero re-verification needed.

The sitemap has **402 URLs** as of this session, all on `orthodoxoskomvos.gr` (no `workers.dev` leakage).

## JSON-LD enhancements landed in commit `e026afb` (2026-05-14)

These changes built on top of the SEO.md baseline:

### Article schema (`src/pages/articles/[...slug].astro`)
Now emits:
- `image` — absolute URL of `/og-default.png`
- `publisher` — Organization with site URL
- `mainEntityOfPage` — WebPage `@id` matching canonical
- `dateModified` — emitted IFF the entry has the optional `updatedDate` frontmatter field

Google requires `image` and `publisher` for Article rich-result eligibility, and `mainEntityOfPage` resolves the WebPage ↔ Article entity properly.

### News pages (`src/pages/news/index.astro`, `src/pages/news/[date].astro`)
Now emit `CollectionPage` + `ItemList` JSON-LD where each `ListItem.url` points to the **external news source**. This is the correct schema for an aggregator that links off-site — `NewsArticle` would be wrong because we don't author the news.

### Related-articles block (`src/pages/articles/[...slug].astro`)
Every article page now shows a "Σχετικά" aside with up to 4 peer articles, ranked by (a) shared-tag count then (b) recency. Falls back to "most recent peers" when the current article has no tags. Improves crawl depth and dwell-time signal.

### Schema additions (`src/content.config.ts`)
Added optional `updatedDate: z.coerce.date().optional()` to both `articles` and `erminies` collections. To use it, add `updatedDate: 2026-05-14` to the frontmatter of any article you genuinely revise — that emits `dateModified` in the Article JSON-LD and is a freshness signal.

## What's NOT yet wired (deferred)

- **Organization logo** — no dedicated logo asset exists; `publisher` JSON-LD omits the `logo` sub-object. If/when a square brand mark is created, add it to `publisher.logo` as an ImageObject.
- **Speakable schema** — only worth adding if targeting voice assistants.
- **Greek directories** — not a thing for Greek SEO; Google holds ~95% of Greek search. Skip.

## Wired since 2026-05-14 (commit 25f4b70 and prior)

### Per-article hero image
- Schema: `articles` and `erminies` collections both accept optional `image: z.string().optional()` field (root-relative path under `public/`).
- Plumbing: `src/pages/articles/[...slug].astro` and `src/pages/bible/erminies/[slug].astro` pass `ogImage={entry.data.image ?? '/og-default.png'}` to `BaseLayout`.
- Falls back to brand default automatically.
- Adding `image: /path/to/hero.jpg` to an article frontmatter is now a no-code operation.
- **Recommended dimensions**: 1200×630 (1.91:1). BaseLayout emits `og:image:width=1200, og:image:height=630` unconditionally — if the hero image has a very different aspect, FB/LinkedIn either crop or fall back to small thumbnail. Use this aspect or generate a composite card.

### Per-saint OG composite card (1200×630 JPEG)
- **Problem (2026-05-14)**: saint pages used to emit raw Wikimedia `iconUrl` as `og:image`. Those icons are portrait, FB/LinkedIn forced them into the 1.91:1 landscape card → ugly center-crop. Hardcoded `og:image:width=1200, height=630` meta in BaseLayout made it worse (Cloudfare-side scrapers trusted the lied dimensions).
- **Fix**: `scripts/_make_og_cards.py` composes a per-saint 1200×630 JPEG: parchment-gradient canvas with the icon framed on the left + name + feast date on the right + `orthodoxoskomvos.gr` brand mark at bottom-center. Output → `public/og/saints/<slug>.jpg`.
- **Plumbing**: `src/pages/saints/[...slug].astro` now derives `ogImagePath = entry.data.iconUrl ? /og/saints/<id>.jpg : /og-default.png`. The composite is always 1200×630 so the BaseLayout dimensions meta is honest.
- **Idempotent**: re-run skips existing files. Add `--force` to rebuild all, or `--slug <slug> --force` to rebuild one (after editing frontmatter).
- **Rate-limited**: Wikimedia 429s aggressively at >5 req/sec. The script ships with 0.5s inter-request delay + 2 workers + 429-aware retry — full 463-saint regen takes ~4–5 min.
- **JPEG quality 85** keeps each card ~85 KB. Full 463-saint set = ~40 MB in repo, within Cloudflare Workers + Static Assets limits.
- **Mandatory before every commit** that adds/edits saints — encoded in the `add-saint` skill as a hard gate alongside `fetch_icon.py`.
- **Fonts**: prefers `georgia.ttf`/`georgiab.ttf` for polytonic Greek glyph coverage; falls back to DejaVu, then PIL default.

### Sitemap per-entry `lastmod`
- `astro.config.mjs` builds a `Map<route, ISODate>` at config-load time by reading the `pubDate`/`updatedDate` fields from `articles/*` and `erminies/*` frontmatter (regex-extracted, no YAML lib needed).
- The `serialize` callback in `@astrojs/sitemap` looks up each emitted item against that map.
- Verified in `dist/client/sitemap-0.xml`: every `/articles/*` and `/bible/erminies/*` entry has its own `<lastmod>` from its frontmatter date; non-content pages still default to build time.
- Adding `updatedDate: YYYY-MM-DD` to an article frontmatter automatically refreshes its sitemap `lastmod` on next build.

### OG image cachebusting (FB / LinkedIn fix)
- `BaseLayout.astro` appends `?v=<token>` to the brand-default og:image URL via `OG_DEFAULT_CACHEBUSTER`. Current token: `2026-05-14`.
- Per-article custom images are left unversioned (their URL changes per entry).
- **WHY**: FB and LinkedIn cache the **image bytes** keyed on the og:image URL. Re-deploying `og-default.png` at the same path does NOT trigger refresh — those scrapers keep serving the old bytes for ~7 days. Changing the URL via query string forces a fresh fetch.
- **WHEN TO BUMP** `OG_DEFAULT_CACHEBUSTER`: whenever `public/og-default.png` content actually changes (brand rename, redesign, tagline change). Don't bump for unrelated commits.

### Brand name is hardcoded in `scripts/_make_og_default.py`
- Line ~82: `title = "Ορθόδοξος Κόμβος"` (was "Ορθόδοξος Λόγος" pre-2026-05-14 rebrand).
- Line ~88: `tagline = "Πατερικά κείμενα · Βίοι αγίων · Ακολουθίες"`.
- After editing, re-run: `scripts/venv/Scripts/python.exe scripts/_make_og_default.py`.
- THEN bump `OG_DEFAULT_CACHEBUSTER` in BaseLayout.
- Pillow is required in the venv (`pip install Pillow`).
- Caught 2026-05-14 — FB/LI previews kept showing "Ὀρθόδοξος Λόγος" weeks after the site renamed to "Ὀρθόδοξος Κόμβος".

## FB / LinkedIn share troubleshooting decision tree

| Symptom user reports | Likely root cause | Fix |
|---|---|---|
| "FB share button shows 'User opted out of platform'" | **Personal FB account setting** — not a site issue. Sharer.php refuses to act for accounts that disabled platform integrations. | User goes to https://accountscenter.facebook.com → Connections → Apps and websites → toggle ON. Verify by opening sharer URL in a private window. |
| "FB preview shows old brand/old image even after Scrape Again" | FB image cache keyed on og:image URL. HTML refreshed but image bytes are stale. | Bump `OG_DEFAULT_CACHEBUSTER` in BaseLayout, redeploy, scrape again. |
| "LinkedIn share has no preview image" | LinkedIn image cache; same mechanism as FB. | Same cachebuster fix. Then https://www.linkedin.com/post-inspector/ → Inspect to force re-fetch. |
| "LinkedIn share for a saint shows the icon but cropped/squished" | Old wiring: saint page emitted raw portrait Wikimedia URL as og:image. Pre-2026-05-15 fix. | Run `_make_og_cards.py` (now emits 1200×630 composite). Then Post Inspector for that saint URL. |
| "LinkedIn share for an article without `image:` set shows tiny brand thumbnail" | LinkedIn cached the page when og:image was missing/different; their cache outlives our cachebuster sometimes. | LinkedIn Post Inspector → Inspect URL → "Refresh". One-shot per URL. |
| "FB preview shows literal 'null' in title or description" | Either og:title is empty (verify with curl + facebookexternalhit UA) OR FB cached a pre-OG-tags scrape. | Check curl output; if tags exist, just Scrape Again on FB Debugger. |
| "Share opens FB but title/description are blank" | Mobile FB app behavior — sometimes pre-population fails on iOS/Android even when og tags are correct. | Limited fix; FB controls the in-app composer. og:site_name + og:type=article help. |

## Cloudflare cache tier — corrections

**Cache Reserve is PAID** (caught 2026-05-14, earlier note was wrong). It's a separate add-on with storage + operations billing.

For **free** TTFB improvements on Pages/Workers deployment:

| Feature | Where | Cost | Why |
|---|---|---|---|
| **Smart Tiered Caching Topology** | Caching → Tiered Cache | Free | Routes requests through Cloudflare's regional cache hierarchy; bigger origin-shield effect. The "Origin Configuration" sub-widget under it sometimes throws a transient UI error — ignore, the topology toggle is what matters. |
| **Cache Rules for static assets** | Rules → Cache Rules | Free | Match `\.(css\|js\|png\|svg\|woff2\|ico)$` → Edge TTL 1 month, Browser TTL 1 month. |
| **Brotli + Early Hints** | Speed → Optimization → Content | Free | Already on per the zone-settings table. |
| ~~Cache Reserve~~ | ~~Caching → Cache Reserve~~ | ~~PAID~~ | Skip on free tier. |
| ~~Argo Smart Routing~~ | ~~Network~~ | ~~PAID~~ | Skip. |

## Email Routing — two-stage activation gotcha

Cloudflare Email Routing has a **separate master switch** from the address-creation flow. The UI lets you create custom addresses (e.g. `info@yourdomain.gr`) before the routing engine is enabled, then displays a "not routing emails due to misconfigured domain" warning on the address row.

Activation sequence:
1. Dashboard → Email → Email Routing → **Overview** tab.
2. Click the "**Enable Email Routing**" link in the orange banner at the top (or the equivalent CTA).
3. Cloudflare auto-creates the MX + TXT records on the zone (route1/2/3.mx.cloudflare.net + SPF + DKIM).
4. Wait ~30 sec for the "Missing" badges on those records to turn green/Active.
5. Verify destination email in Gmail (confirmation link from Cloudflare).
6. *Now* the custom address you previously created starts routing. The triangle warning on that row disappears.

If "Enable Email Routing" is missing entirely: check DNS → Records for stale MX entries from old hosting, delete those first, then revisit.

Catch-all rule recommended: route `*@yourdomain.gr` → same Gmail destination, so typos (`info@`, `contact@`, `epafi@`) don't bounce.

## Push workflow — gotchas

```bash
# Bots commit to main on schedule (daily-saints 03:00 UTC, news every 6h).
# ALWAYS rebase before pushing to avoid rejection:
git pull --rebase origin main
git push origin main
```

The `recover-from-bot-push` skill handles the rejection case if you forget.

On Windows, embedded `"..."` quotes in `git commit -m` strings break in PowerShell — use Bash tool or HEREDOC via `git commit -F .git/COMMIT_EDITMSG`. (Captured in user's global memory `feedback_powershell_git_commit.md`.)

## Validation commands

```powershell
# After deploy, check rich-results eligibility on an article:
# (open in browser — no Bash needed)
https://search.google.com/test/rich-results?url=https://orthodoxoskomvos.gr/articles/theosis/

# Local build sanity:
npm run build    # should produce 424 pages + sitemap-index.xml + pagefind/

# Live sitemap check:
https://orthodoxoskomvos.gr/sitemap-index.xml    # XML index pointing at sitemap-0.xml
https://orthodoxoskomvos.gr/sitemap-0.xml        # 402 URL entries
```

## Where things live (post-launch)

| What | Where |
|---|---|
| SEO baseline reference (pre-launch architecture) | `SEO.md` (root) |
| Deployment playbook (pre-launch) | `DEPLOY.md` (root) |
| Post-launch operational state | THIS skill |
| All meta tags + JSON-LD orchestration | `src/layouts/BaseLayout.astro` |
| Article schema + Related block | `src/pages/articles/[...slug].astro` |
| Person schema (saints, fathers) | `src/pages/saints/[...slug].astro`, `src/pages/fathers/[...slug].astro` |
| ItemList schema (news) | `src/pages/news/index.astro`, `src/pages/news/[date].astro` |
| Collection schemas (incl. `updatedDate`) | `src/content.config.ts` |
| Node version pin | `.nvmrc` (22.12.0) |
| robots.txt (repo copy) | `public/robots.txt` |
| Brand OG image generator | `scripts/_make_og_default.py` |
| Per-saint OG card generator | `scripts/_make_og_cards.py` → `public/og/saints/<slug>.jpg` |

## Cost (post-launch)

€0/year + domain renewal (~€18-25/year via Papaki).
