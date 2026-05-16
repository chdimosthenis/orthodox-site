"""PostToolUse hook — regenerate the OG share card after a saint .md edit.

Wired in `.claude/settings.json` under `hooks.PostToolUse` with matcher
`Edit|Write`. Reads the tool event JSON from stdin, no-ops unless:

  1. The edited file is `src/content/saints/<slug>.md`
  2. The affected text mentions one of the card-relevant frontmatter
     fields (`iconUrl:`, `feastDay:`, `name:`) — skips pure body edits
     so casual prose tweaks don't burn 3-4s per Edit.

When both conditions hold, runs:
  scripts/venv/Scripts/python.exe scripts/_make_og_cards.py \
      --slug <slug> --force

Output goes to stderr so Claude can see what happened. The hook never
blocks the tool result (PostToolUse can't undo the edit anyway).

This is the deterministic path. The `regenerate-og-cards` skill is the
heuristic path (Claude reading the description and choosing to invoke).
Both ship — hook for Claude-edits, skill for batch flows where Claude
runs a Python script (fetch_icon.py / daily_seed.py) which the hook
can't catch.
"""
from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SAINTS_DIR = ROOT / "src" / "content" / "saints"
SCRIPT = ROOT / "scripts" / "_make_og_cards.py"
VENV_PY = ROOT / "scripts" / "venv" / "Scripts" / "python.exe"

# Frontmatter fields whose change requires re-rendering the OG card.
# Skip purely body-text edits to avoid wasting time on every prose tweak.
CARD_FIELDS = ("iconUrl", "feastDay", "name")


def log(msg: str) -> None:
    """Hook output to stderr — shows up in Claude's transcript."""
    print(f"[regen-og-card] {msg}", file=sys.stderr)


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # invoked outside CC — silently no-op

    tool_name = event.get("tool_name", "")
    if tool_name not in ("Edit", "Write"):
        return 0

    tool_input = event.get("tool_input") or {}
    file_path_raw = tool_input.get("file_path", "")
    if not file_path_raw:
        return 0

    # Must be a saint .md under our content tree
    try:
        path = Path(file_path_raw).resolve()
        path.relative_to(SAINTS_DIR)
    except (ValueError, OSError):
        return 0
    if path.suffix.lower() != ".md":
        return 0

    # Did the edit touch the frontmatter fields the composite uses?
    if tool_name == "Edit":
        haystack = (
            tool_input.get("old_string", "") + "\n" +
            tool_input.get("new_string", "")
        )
    else:  # Write
        haystack = tool_input.get("content", "")

    if not any(f"{f}:" in haystack for f in CARD_FIELDS):
        return 0

    slug = path.stem

    # Sanity: venv + script must exist
    if not VENV_PY.exists():
        log(f"WARN skipped {slug}: venv missing at {VENV_PY}")
        return 0
    if not SCRIPT.exists():
        log(f"WARN skipped {slug}: script missing at {SCRIPT}")
        return 0

    log(f"regenerating public/og/saints/{slug}.jpg ...")
    try:
        result = subprocess.run(
            [str(VENV_PY), str(SCRIPT), "--slug", slug, "--force"],
            cwd=str(ROOT),
            timeout=60,
            capture_output=True,
            text=True,
        )
    except subprocess.TimeoutExpired:
        log(f"TIMEOUT after 60s for {slug} — Wikimedia probably rate-limited")
        return 0
    except OSError as e:
        log(f"OSError invoking subprocess: {e}")
        return 0

    if result.returncode != 0:
        # Don't block the tool result — PostToolUse can't undo the edit.
        log(f"regen failed for {slug}: {(result.stderr or '').strip()[:240]}")
        return 0

    # Compact success summary
    for line in (result.stdout or "").splitlines():
        line = line.strip()
        if line:
            log(line)
    log(f"done — {slug}.jpg refreshed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
