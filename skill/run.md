# run — batch process pending inbox

> **Skill directory note:** This file is in the skill directory (e.g. `<skill-dir>/`, `~/.claude/skills/pin-llm-wiki/`, `~/.copilot/skills/pin-llm-wiki/`, or `~/.cursor/skills/pin-llm-wiki/`). All `templates/` and sibling-file paths below are relative to that same directory. Use whichever path applies to the tool that loaded this skill.

## Invocation forms

```
/pin-llm-wiki run              ← batch: process all pending items
/pin-llm-wiki run <url>        ← single: process only this URL from Pending
```

When a `<url>` argument is supplied, `run` operates in **single-URL mode**: only the inbox line whose URL exactly matches `<url>` is processed. Pass 1 processes only that one line; Pass 2 (refresh) runs normally (all `<!-- refresh -->` lines in Completed). All other behavior — fetch, ingest, lint, summary report — is identical.

**Single-URL error cases** (stop immediately, do not proceed):
- URL not found under `## Pending` → "URL not found in Pending: `<url>`. Add it with `/pin-llm-wiki queue <url>` first."
- URL found under `## Pending` but has `<!-- skip -->` tag → "URL is marked `<!-- skip -->` — remove the tag from `inbox.md` to process it."
- URL found under `## Completed` (already ingested) → "URL already completed. To re-fetch, add `<!-- refresh -->` to its inbox line and run `/pin-llm-wiki run` again."

---

## Guard

Check whether `.pin-llm-wiki.yml` exists in the current working directory. If not, stop:
> "No wiki found here (`.pin-llm-wiki.yml` missing). Run `/pin-llm-wiki init` to scaffold one first."

---

## Setup

Read `.pin-llm-wiki.yml` and extract: `domain`, `detail_level`, `source_types`, `auto_mark_complete`, `auto_lint`.

Set `today` = current date in `YYYY-MM-DD` format.

Initialize a **run log** (empty list): `{pass, url, slug, outcome}` entries appended as each item completes.

---

## Pass 1 — Process pending items

Read `inbox.md`. Collect all lines matching `- [ ] ...` under `## Pending`, in order top-to-bottom.

**In single-URL mode:** filter the collected lines to only the one line whose URL matches the `<url>` argument. If after filtering the list is empty, the error-case checks above already fired — this point is not reached.

For each such line:

### 1. Skip check

If the line contains `<!-- skip -->`: append `{pass: 1, url: <url>, outcome: skipped}` to the run log, leave the line as-is, continue to next.

### 2. Parse the line

Extract:
- **URL** — first token after `- [ ] `
- **Tags** — `<!-- detail:X -->`, `<!-- branch:X -->`, `<!-- clone -->` if present

### 3. Effective detail level

`<!-- detail:X -->` override if present; else `detail_level` from config.

### 4. Source type detection

| Pattern | Type |
|---|---|
| `github.com/<org>/<repo>` — exactly two non-empty path segments | `github` |
| `youtube.com/watch?v=` or `youtu.be/<id>` | `youtube` |
| anything else | `web` |

### 5. Slug and raw path derivation

Same rules as `add`:

- **GitHub:** slug = `<org>-<repo>`, raw path = `raw/github/<org>-<repo>.md`
- **YouTube:** video ID from URL; title slug finalized after fetch step 1 (requires `yt-dlp --dump-json` output); full slug = `<video-id>-<title-slug>`; raw path = `raw/youtube/<video-id>-<title-slug>.md`
- **Web:** slug = hostname with `www.` stripped (preserve subdomains); raw path = `raw/web/<domain>.md`

### 6. Fetch

Read the protocol file for the detected type and follow it exactly:
- GitHub → `<skill-dir>/templates/protocols/github.md`
- YouTube → `<skill-dir>/templates/protocols/youtube.md`
- Web → `<skill-dir>/templates/protocols/web.md`

Apply `<!-- branch:X -->` and `<!-- clone -->` tags (GitHub only). Use the effective detail level.

**Fetch failure handling:**

| Failure | Action |
|---|---|
| YouTube, no transcript | Flag line with `<!-- fetch-failed:no-transcript -->`. Leave in `## Pending`. Append `{pass: 1, url, outcome: fetch-failed:no-transcript}` to run log. Continue to next item. |
| 200k token guard | Cumulative input tokens for this source approaches 200k → halt the entire run, surface to user. Do not continue to remaining items. |
| Other error | Log the error. Leave line in `## Pending` unchanged. Append `{pass: 1, url, outcome: fetch-error: <reason>}` to run log. Continue to next item. |

### 7. Ingest

Read `<skill-dir>/ingest.md` and follow its instructions.

Pass this context:

| Variable | Value |
|---|---|
| `slug` | derived above (YouTube: finalized after fetch step 1) |
| `type` | `github` / `youtube` / `web` |
| `raw_file_path` | derived above |
| `effective_detail_level` | override or config default |
| `auto_mark_complete` | from config |
| `today` | current date |

Ingest step 9 is a no-op for git—do not run `git commit` for ingest (see the wiki’s `AGENTS.md` **Git — never auto-commit**).

Append `{pass: 1, url, slug, outcome: ingested}` to run log.

### 8. Re-read inbox before next item

`inbox.md` was mutated by ingest step 8. Re-read it before processing the next pending item to pick up the updated state.

---

## Pass 2 — Refresh tagged items

Re-read `inbox.md`. Collect all lines under `## Completed` that contain `<!-- refresh -->` (regardless of `[ ]` / `[x]` state), in order.

For each such line, run the **refresh flow**:

### 1. Resolve slug and raw path

Extract URL and any type-detection tags. Detect source type (same rules as Pass 1). Derive slug and `raw_file_path` (same rules as Pass 1).

For **YouTube**: the full slug includes the title, which is encoded in the raw filename. Scan `raw/youtube/` for files whose name starts with `<video-id>-`. If exactly one match: use its full name as the slug. If zero matches: report error ("raw file for <video-id> not found — was this source ever ingested?") and skip. If more than one match: report error ("ambiguous raw files for <video-id>: <list>") and skip.

### 2. Read existing raw file

Read `raw_file_path` fully into memory (this is the "before" state).

### 3. Re-fetch

Read the protocol file for the detected type and re-fetch using the same protocol. Do not overwrite the raw file yet — hold the new content in memory.

### 4. Compare

Strip from both the old and new content any frontmatter fields whose value is a date or timestamp that changes on every fetch (any field whose value matches `YYYY-MM-DD` or an ISO 8601 timestamp pattern). Compare the remainder.

**If content is identical:**
- Record `refresh: <slug> (no change)` in the run log only — do not write to `wiki/log.md`.
- Proceed to step 5.

**If content differs:**
- Overwrite `raw_file_path` with the new fetched content.
- Run ingest steps 2–5 and 7 (re-create/update `wiki/sources/<slug>.md`, `wiki/index.md`, `wiki/overview.md`, `raw/<type>/README.md`). Skip step 6 — the refresh log entry is written below instead. Skip step 8 (inbox line is already in `## Completed`) and step 9 (commit is done after step 5).
- Append to `wiki/log.md` immediately below the heading (newest at top):
  ```
  ## <today> | refresh | <slug> | content updated

  - Updated: wiki/sources/<slug>.md, wiki/index.md, wiki/overview.md, wiki/log.md
  - Raw: raw/<type>/<slug-file>.md
  ```
- Proceed to step 5.

### 5. Update inbox line

- Remove `<!-- refresh -->` from the line.
- Append `<!-- refreshed <today> -->`.
- Preserve the existing `[ ]` / `[x]` state.
- Write the updated `inbox.md`.
- **Do not** run `git commit` or `git push` (see the wiki’s `AGENTS.md` **Git — never auto-commit**).

Append `{pass: 2, url, slug, outcome: refreshed | no-change}` to run log.

---

## Post-run lint

If `auto_lint: batch`: read `<skill-dir>/lint.md` and run the full lint. Include the lint report in the run output below.

If `auto_lint: never` or `per-ingest`: skip lint. Per-ingest lint is suppressed when running in batch mode — lint fires once at the end (`batch`) or not at all (`never`). It never fires per-item inside `run`.

---

## Summary report

Print:

```
run complete — <domain> wiki
<today>

Pass 1 — pending:
  Ingested: N
  Skipped:  N  (<!-- skip --> tag)
  Failed:   N  (fetch errors logged above)

Pass 2 — refresh:
  Updated:   N
  No change: N

[Lint: <N ERROR, N WARN, N INFO — see report above>]
[Lint: skipped (auto_lint: <never|per-ingest>)]
```

---

## Notes

- **Idempotency:** items remain under `## Pending` until successfully ingested. A crashed run can be safely re-run — it picks up from the first item still under `## Pending`.
- **No agent commits:** ingest and refresh never run `git commit`—the human commits after review.
- **`<!-- skip -->` is persistent:** the tag remains on the line and `run` skips it on every subsequent invocation. Remove the tag manually to process the item.
- **Partial raw content on crash:** if a run crashes mid-fetch, the partial raw file (if any) will be overwritten on the next run's re-fetch — no manual cleanup needed.
