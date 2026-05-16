---
name: orthodoxoskomvos-orientation
description: Master orientation for the Ὀρθόδοξος Κόμβος site (orthodoxoskomvos.gr). Encodes repo location, content-collection map, voice/register conventions per type, deployment target (Cloudflare Pages), build/commit cadence, and which sub-skill to call for each kind of operation. Use as the FIRST skill in any session that mentions the orthodox site, ορθοδοξία content, polytonic Greek liturgical text, or any path under C:\Users\dimos\Documents\orthodox-site. Routes to add-saint / add-father / add-article / add-erminia / fix-icon / editorial-pass / subagent-permissions / fewer-permission-prompts / etc.
---

# Ὀρθόδοξος Κόμβος — operating context

## Repo

```
C:\Users\dimos\Documents\orthodox-site
```

Production: `https://orthodoxoskomvos.gr` (Cloudflare Workers + Static
Assets, auto-deploys from `main`). Worker fallback URL:
`https://orthodoxoskomvos.dimos-chatzinikolaou.workers.dev`.

GitHub: `chdimosthenis/orthodoxoskomvos` (private? — check).

## Stack

- Astro 6 static site generator
- TypeScript content collections with Zod schema (`src/content.config.ts`)
- Pagefind for full-text search
- Cloudflare Pages free tier (no API costs, no monthly fees)
- News auto-fetch every 6h via `.github/workflows/news.yml`
  (RSS only — NO Anthropic API)

## Content collections — the canonical map

| Collection | Path | Register | Voice exemplar |
|---|---|---|---|
| `articles`   | `src/content/articles/`   | Modern Greek **monotonic** | `articles/proseyhi-iisou.md` |
| `erminies`   | `src/content/erminies/`   | Modern Greek **monotonic** | `articles/proseyhi-iisou.md` |
| `fathers`    | `src/content/fathers/`    | **Polytonic** Greek strictly | `fathers/grigorios-palamas.md` |
| `saints`     | `src/content/saints/`     | Polytonic frontmatter, body either way | hand-curated batch |
| `liturgical` | `src/content/liturgical/` | Polytonic for prayers; intros either | `liturgical/symvolon-pisteos.md` |
| `bible`      | `src/content/bible/`      | Polytonic NT (Patriarchal Text 1904) | `bible/kata-matthaion.md` |

## Routing

```
/                                home (TodaysEortologio widget + NewsWidget + recent articles)
/news                            latest news snapshot (auto-archived per day)
/news/archive                    list of all dated news archives
/news/<YYYY-MM-DD>               specific day's snapshot
/bible                           hub: 2 cards (Πλῆρες Κείμενο + Ἑρμηνεῖες)
/bible/keimeno                   27 NT books listing
/bible/<book>                    one NT book
/bible/erminies                  ermineia listing
/bible/erminies/<slug>           one ermineia
/didaskalia                      hub: Ἄρθρα + Θεολογία + Ἱστορία
/articles                        flat articles index
/theology                        + /theology/<cluster>
/history                         + /history/<cluster>
/prosopa                         hub: Ἅγιοι + Πατέρες
/saints                          chronological by reposeYear
/fathers                         chronological by century
/latreia                         hub: Ἀκολουθίες + Ἑορτολόγιον + Μοναστήρια + Ναὸς&Λατρεία + Προσευχητάριον + Ὕμνοι
/akolouthies, /ymnoi, /proseuxitari    (separate listings)
/eortologio                      static calendar of feasts
/monasteries                     static index of major monasteries
/naos-kai-latreia                + 3 sub-sections
/search                          Pagefind UI (noindex)
/about                           about page with AI-disclaimer + non-profit mission
```

## Build + commit cadence

```
npm run build          # always verify before commit
git add <specific-paths>   # NOT git add -A unless you've reviewed
git commit -m "<scope>: <imperative>

<body — list actual fixes, not prose>"
git pull --rebase origin main      # ALWAYS — bot pushes daily
git push
```

## Bot collisions

`.github/workflows/news.yml` runs every 6h and bot-pushes to `main`.
Always `git pull --rebase` before `git push`. The `recover-from-bot-push`
skill encodes the recovery if you forget.

## Sub-agent unlock

Sub-agents can't write to the project unless `.claude/settings.json`
explicitly allows it. The unlock is committed to this repo at
`.claude/settings.json`. If a fresh sub-agent reports "Write denied",
trigger the `subagent-permissions` skill.

## Routing table — which skill for which task

| User says... | Skill |
|---|---|
| "πρόσθεσε τὸν ἅγιο/ὁσίαν..." | `add-saint` |
| "πρόσθεσε Πατέρα τῆς Ἐκκλησίας" | `add-father` |
| "γράψε ἑρμηνεία τῆς παραβολῆς..." | `add-erminia` |
| "γράψε ἄρθρο γιὰ τὴ νοερὰ προσευχή..." | `add-article` |
| "ἐπιμελητικὸ πέρασμα στοὺς Πατέρες" | `editorial-pass` |
| "διόρθωσε τὶς εἰκόνες ποὺ δὲν φορτώνουν" | `fix-icon` |
| "ξαναφτιάξε τὶς κάρτες κοινωνικῆς δικτύωσης" / "regenerate og cards" / "rebuild saint cards" | `regenerate-og-cards` (also fires automatically after every `add-saint` / `fix-icon` / `bulk-seed-and-publish`) |
| "πάρε νέες προσευχὲς ἀπὸ glt.goarch.org" | `fetch-akolouthia` |
| "ἀπόψε push δὲν περνᾶ — bot conflict" | `recover-from-bot-push` |
| "agents can't write" / "Write denied" | `subagent-permissions` |
| "διπλὰ permission prompts ἐνοχλοῦν" | `fewer-permission-prompts` |
| "deploy" / "hosting" / "SEO" / "Search Console" / "Bing" / "Cloudflare zone" / "robots" / "sitemap" | `deployment-and-seo` |

## Domain + SEO state (LIVE since 2026-05-14)

The site is live at `https://orthodoxoskomvos.gr`. Hosted on Cloudflare
Workers + Static Assets (fallback URL: `*.workers.dev`, NOT `*.pages.dev`).
GSC + Bing both wired; sitemap (402 URLs) submitted to both. Article
JSON-LD now includes image/publisher/mainEntityOfPage/dateModified
(via optional `updatedDate` frontmatter). News pages emit CollectionPage
+ ItemList (correct aggregator schema — items link off-site). Every
article page has a Σχετικά block ranking peers by tag-overlap then recency.

**For deployment, SEO, Cloudflare-zone, or search-indexation work, read
the `deployment-and-seo` skill — it captures the post-launch operational
state.** DEPLOY.md and SEO.md describe the pre-launch architecture and
are still accurate as architecture references, but the operational state
(Cloudflare zone settings done, Bing import-from-GSC, robots.txt vs
Cloudflare AI bot overrides, etc.) lives in the skill.

## Cost

€0/year operating cost (Cloudflare free tier). Domain renewal ~€18-25.
No Anthropic API costs — all content is hand-authored or RSS-aggregated.
