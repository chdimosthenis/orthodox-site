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

- **Per-article hero image** — articles JSON-LD currently uses `og-default.png` for `image`. Add a per-article `image` frontmatter field + plumb through `ogImage` prop when articles start getting hero images.
- **Organization logo** — no dedicated logo asset exists; `publisher` JSON-LD omits the `logo` sub-object. If/when a square brand mark is created, add it to `publisher.logo` as an ImageObject.
- **Speakable schema** — only worth adding if targeting voice assistants.
- **Greek directories** — not a thing for Greek SEO; Google holds ~95% of Greek search. Skip.

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
| OG image generator | `scripts/_make_og_default.py` |

## Cost (post-launch)

€0/year + domain renewal (~€18-25/year via Papaki).
