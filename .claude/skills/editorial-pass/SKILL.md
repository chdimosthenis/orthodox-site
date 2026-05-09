---
name: editorial-pass
description: Run a "best Greek Orthodox patrologist + Greek philologist combined" editorial pass on Greek-language content using a THREE-PASS procedure per file (Pass 1 substantive correctness → Pass 2 Greek language → Pass 3 polish/consistency). Each file goes through all three lenses sequentially within the same agent invocation — keeps content in context, catches interactions one-pass review misses. Encodes the agent prompt template, the polytonic-vs-monotonic register rules per content type, the patristic-quote verification protocol, per-pass focus areas, the fallback when sub-agent Edit is denied (patch-script pattern), and the "what NOT to touch" preservation rules. Triggers when the user asks for an "ἐπιμελητικὸ πέρασμα", "editorial review", "γλωσσικό πέρασμα", "πατερικὴ ἀκρίβεια", "ἔλεγχος δογματικῆς ἀκρίβειας", or names a content directory and asks for proofreading by a Greek-Orthodox-scholar persona.
---

# Editorial pass on Greek-Orthodox content (THREE-PASS)

Run a combined patrologist + Greek philologist pass. Each file gets
THREE sequential passes within the same agent invocation. Read once,
apply three lenses with surgical edits.

The three passes catch:

- **Pass 1 — Substantive correctness**: patristic-quote attribution,
  Western theological drift, historical-fact accuracy, hagiographic
  accuracy
- **Pass 2 — Greek language correctness**: polytonic/monotonic accents
  & breathings, gender/case/number agreement, verb forms, spelling
- **Pass 3 — Polish and consistency**: internal terminology consistency,
  surgical prose-flow, final integrity check after Passes 1-2

Why three sequential passes per file (not three file walks)? Keeping
content in context for all three lenses catches interactions a one-pass
review misses — fixing an attribution often surfaces a grammar issue
in the corrected wording, and Pass 3 catches both.

## What each pass targets

### Pass 1 — Substantive correctness

- **Patristic-quote attribution**. Verify against safe-list (Chrysostom
  on Matthew/John homilies; Νύσσης on Beatitudes; Μάξιμος Ὁμολογητής on
  dogmatic; Συμεὼν Νέος Θεολόγος on inner life; Παλαμᾶς on Tabor light).
  Convert unverifiable quotes to paraphrase ("ὁ Χρυσόστομος ἑρμηνεύει
  αὐτὸ ὡς…").
- **Western theological drift**. Catch and correct:
  - μετουσίωση (transubstantiation) → μεταβολή
  - ἀνεξάλειπτο σημεῖο (indelible character) → σφραγίδα τοῦ Πνεύματος
  - filioque undertones in Trinitarian language
  - juridical-atonement framings → ontological / healing
  - Immaculate-Conception phrasings on Παναγία
  - papal-primacy / sola-fide / scholastic terminology
- **Historical-fact errors**. Council years, bishop counts, repose
  dates, biographies, attendance at synods, episcopal titles.
- **Hagiographic accuracy**. Correct attribution of acts to saints,
  patronymics, episcopal seats, miracles correctly attributed (e.g.
  Spyridon Trimythountos married not monk; Loukas Συμφερουπόλεως
  surgeon — different from Loukas the Evangelist).

### Pass 2 — Greek language correctness

Per-collection register (see table below).

- **Polytonic** (`fathers/`, prayers in `liturgical/`, saints
  frontmatter): smooth/rough breathings (ψιλή/δασεῖα), acute/grave/
  circumflex on the right syllable, iota subscripts on dative
  singulars, reflexive pronouns (ἑαυτοῦ vs αὐτοῦ).
- **Monotonic** (`articles/`, `erminies/`): single-tonal correctness,
  modern grammatical idiom.
- Gender / number / case agreement (κι ἡ / καί ή; τὸν αὐτὸν vs τὸ αὐτό).
- Verb mood, tense, aspect (ἐποίησεν vs ἐποίησε).
- Spelling and non-words (Vladimir's "πολυλάτρης" — Wave 2 catch).

### Pass 3 — Polish and consistency

- Internal terminological consistency within the file (don't switch
  between μυστήριον / σακράμεντο / ἱερὸ μυστήριο in one entry).
- Cross-file terminology drift — note for batch summary if widespread.
- Surgical prose-flow fixes — only obvious clunkers, never restyling.
- **Final integrity check** — verify Passes 1-2 edits didn't introduce
  new issues. A corrected attribution often needs grammar adjustment.

## Per-collection register

Run ONE agent per content type — never mix.

| Collection                 | Register      | Body shape                                | Voice exemplar |
|----------------------------|---------------|-------------------------------------------|----------------|
| `src/content/articles/`    | Modern monotonic Greek | Free prose, sectioned with `##`           | `articles/proseyhi-iisou.md` |
| `src/content/erminies/`    | Modern monotonic Greek | Intro + `## Τὸ νόημα` + `## Πατερικὲς προσεγγίσεις` (+ optional `## Ἐφαρμογή`) | `articles/proseyhi-iisou.md` |
| `src/content/saints/`      | Polytonic Greek (frontmatter) + body either way | Frontmatter `name`, `life`, `tropar`, `kontak`; body free prose | hand-curated batch in `src/content/saints/` |
| `src/content/fathers/`     | **Polytonic Greek** strictly | `## Βίος` + `## Διδασκαλία` + `## Σημασία` | `fathers/grigorios-palamas.md` |
| `src/content/liturgical/`  | Polytonic for prayers, monotonic OK for intros | Mixed — prayers are sacred, intros are explanatory | `liturgical/symvolon-pisteos.md` |

The liturgical collection is special: **edit ONLY the explanatory/intro
prose**. Never touch the prayer/hymn/Gospel/quote text itself.

## Agent prompt template

The patrologist+philologist persona has been validated this session. Use
this exact template (substitute the bracketed parts):

```
You are the **best Greek Orthodox [patrologist|hagiographer|biblical-
scholar|liturgist|church-historian] + Greek philologist combined**.
Edit-pass the Greek-language [TYPE] entries at
`C:\Users\dimos\Documents\orthodox-site\src\content\[DIR]\*.md`.

You CAN use Edit tool — project permissions configured.

## What to fix — THREE PASSES per file (sequential)

Each file gets THREE passes in this order:

1. **Pass 1 — Substantive correctness**
   - Patristic-quote attribution drift (convert unsafe to paraphrase)
   - Western theological drift (filioque, μετουσίωση→μεταβολή,
     ἀνεξάλειπτο σημεῖο→σφραγίδα τοῦ Πνεύματος, juridical atonement,
     Immaculate-Conception undertones)
   - Historical-fact errors (council years, bishop counts, repose
     dates, biographies)
   - Hagiographic accuracy (correct attribution of acts to saints)

2. **Pass 2 — Greek language correctness**
   - [register-specific: polytonic accents/breathings OR monotonic
     correctness — see register table for this collection]
   - Gender / number / case agreement
   - Verb mood / tense / aspect / idiom
   - Spelling, non-words

3. **Pass 3 — Polish and consistency**
   - Internal terminological consistency within the file
   - Surgical prose-flow fixes — only obvious clunkers
   - Final integrity check — verify Passes 1-2 edits didn't introduce
     new issues

## What NOT to do
- Don't change `slug` (filename), `pubDate`, `language`, `license`,
  `tags`, `author`, `draft`, `feastDay`, `category`, `iconUrl`,
  `iconAttribution`, `wikipediaTitle`, `reposeYear`, `reposeLabel`,
  `tropar`, `kontak`, `sourceUrl`, `book`, `order`, `division`,
  `chapters`.
- Don't add new content paragraphs/sections.
- Don't reword for stylistic preference — surgical fixes only.
- Don't quote a Father unless you're confident of attribution; convert
  unsupported quotes to paraphrase.
- For `liturgical/`: edit ONLY explanatory/intro prose, NEVER prayer/
  hymn/Gospel/quote text.

## Procedure
1. Glob target files. Filter `language: el` and not `draft: true`.
2. For each file:
   a. Read the file once.
   b. Apply Pass 1 edits.
   c. Apply Pass 2 edits.
   d. Apply Pass 3 edits.
3. After each file, log: "<slug> — P1: <summary> / P2: <summary> /
   P3: <summary>" ('clean' if nothing).
4. After every 5 files, briefly note overall progress.
5. Don't run npm build. Don't commit.

## Reporting
Markdown table under [WORD-LIMIT] words.
| slug | pass 1 | pass 2 | pass 3 |
|------|--------|--------|--------|
| ... | "—" if clean per pass, else short summary capped at ~60 chars |
```

## Real fixes caught this session (calibration data)

- **Wave 1 (31 fathers)**: 17 fixes — 4 historical-fact (council years,
  Athanasius struggle, Diadochos at Chalcedon, Ephraim Παρακλητικὸς
  Κανών), rest polytonic/grammar.
- **Wave 2 (84 saints)**: 38 fixes — Παῦλος 4→3 missionary journeys,
  Stratelates κόλλυβα→Tyron, Spyridon was married not monk, Gregory
  Ἀρχιεπίσκοπος (not Πατριάρχης), Loukas Συμφερουπόλεως patronymic,
  Vladimir non-word "πολυλάτρης", Matrona transliteration; rest
  Greek-grammar / gender-agreement / breathings.
- **Wave 3 (30 erminies)**: 5 fixes — Chrysostom on 1 Cor 13 (3 not 4),
  "μένων ὃ ἦν" misattributed (Gregory the Theologian Or. 29, not
  Chrysostom), Hesychios-quote unverifiable, Pharisee-prayer word count.
- **Wave 4 (88 articles)**: 54 fixes — 2 doctrinal Western drifts caught
  (μετουσίωση→μεταβολή, ἀνεξάλειπτο σημεῖο→σφραγίδα τοῦ Πνεύματος),
  patristic-quote attributions, gender agreements, multiple non-words.
- **Liturgical (42 entries)**: 13 fixes — 5×"Ὧρα"→"Ὥρα", omnipresence
  vs omnipotence ("πανταχοῦ" not "παντοδύναμη"), Σιμωνόπετρα Μονή not
  ἐνορία, Παρρησίαστὸς Κανών non-existent term, "Δυτικὴ" → "Λατινικὴ
  Ἐκκλησία".

These calibration fixes were captured under SINGLE-pass mode. Three-pass
mode is expected to catch ~25-40% more issues per file because Pass 3
re-checks Passes 1-2 outputs and surfaces interaction artifacts.

## Fallback: sub-agent Edit denied

In some sandbox configurations the sub-agent is read-only and Edit is
denied. The recovery pattern:

1. **First**: ensure `.claude/settings.json` has explicit Edit/Write
   allow rules for the project (see the `subagent-permissions` skill).
2. **If still denied**: pivot the agent to write a Python patch script
   instead. The agent enumerates fixes as `(filename, old, new, reason,
   pass_num)` tuples in a script at `scripts/_apply_<wave>_fixes.py`.
   The script reads each file, asserts uniqueness of `old`, applies the
   replacement, writes back. You then run the script. The `pass_num`
   field preserves the per-pass attribution so the commit log can group
   fixes by pass.

## Wave splitting (avoiding usage limits)

THREE-PASS procedure roughly triples the per-file edit budget. An agent
doing one full 3-pass on a file uses ~1 Read + ~3-6 Edits = 4-7 tool
calls per file. With ~40 tool-use budget, expect ~8-12 files per agent.

- **Single-pass mode** (legacy, occasional): ≤25 files per agent
- **Three-pass mode** (default): ≤12 files per agent
- 30+ files in a collection → 3+ agents in parallel
- 60+ files → 5+ agents (parallel pairs to avoid rate-limit collision)
- Run waves SEQUENTIALLY rather than 3+ parallel if budget is tight

For the saints collection (550+ entries), three-pass on all is out of
budget for a single session. Strategy: prioritise newly-seeded entries
(check `pubDate` recent), or sample random 50-100 for QA, or focus on
Wave 2's already-reviewed 84 entries for re-pass.

## Commit cadence

ONE commit per wave. Commit message lists the actual fixes made (not
prose) so future readers can grep history for "ἀκαταπαύστως" or
"μετουσίωση" and find the rationale. Group fixes per pass in the commit
body when feasible:

```
editorial: 3-pass on articles wave A (25 files)

Pass 1 (substantive):
- ...
Pass 2 (Greek language):
- ...
Pass 3 (polish):
- ...
```
