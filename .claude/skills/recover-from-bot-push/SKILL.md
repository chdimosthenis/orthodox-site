---
name: recover-from-bot-push
description: Resolve a `git push` rejection caused by the daily-saints or news-aggregator GitHub Actions bot pushing first. Trigger on "push rejected", "fetch first", "remote contains work that you do not have locally", "[rejected] main -> main", or any failed push from the orthodox-site repo while bots are scheduled.
---

# Recover from a bot push collision

Two cron jobs push to `main` autonomously:

- `daily-saints.yml` — 03:00 UTC daily (writes new commemorations)
- `news.yml` — every 6 hours at :05 (refreshes `src/data/news.json`)

When you push from a session that started before a bot run, the push is
rejected with `! [rejected] main -> main (fetch first)`. The fix is a
clean rebase onto the bot commits.

## Recovery

```bash
cd /c/dev/orthodox-site   # or wherever the repo is
git pull --rebase origin main
git push origin main
```

The local commit is replayed on top of the bot's commit; both end up in
history. Confirm with:

```bash
git log --oneline -5
```

You should see your commit on top, the bot's commit just below
(`chore(bot): seed +N commemorations` or
`chore(news): refresh aggregated feed`).

## When to suspect a bot push

Time-of-day clues:

- ~03:00 UTC = ~05:00–06:00 Athens — daily-saints likely pushed
- :05 of any 6h boundary (00:05/06:05/12:05/18:05 UTC) — news likely pushed

Or just attempt the push: a rejection message confirms it. There's no
need to inspect first.

## Edge cases

- **Conflicting changes**: extremely rare since bots only touch
  `src/content/saints/<new-files>.md` and `src/data/news.json`. If
  rebase reports a conflict, it's almost certainly a coincidental
  overlap on a bot draft you also touched. Resolve manually (keep your
  version on draft files you're publishing, accept theirs on news.json).
- **Stale local view**: if `git status` claims "your branch is up to
  date" but push fails, the local refs are stale. `git fetch origin`
  then retry the rebase.
- **Force push**: never. The bots have committed work; force-push wipes
  it. The rebase is always clean and lossless.

## Prevention (optional)

If you start a long session and want to minimize collisions, do
`git pull --rebase origin main` once at the start. The session's first
commit will land on top of whatever the bots wrote overnight.

## Don'ts

- Don't `git pull` without `--rebase` — that creates a merge commit on
  every collision, polluting history.
- Don't `git push --force` to "fix" the rejection. It deletes the bot's
  commit.
- Don't temporarily disable the bots to "make pushing easier". The
  daily seed and news refresh are core features.
- Don't worry about "losing" the bot's work during rebase. It stays in
  origin; the rebase puts your commit on top of it.
