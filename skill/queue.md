# queue — add URLs to the pending inbox without ingesting

> **Skill directory note:** This file is in the skill directory (e.g. `<skill-dir>/`, `~/.claude/skills/pin-llm-wiki/`, `~/.copilot/skills/pin-llm-wiki/`, or `~/.cursor/skills/pin-llm-wiki/`). All `templates/` and sibling-file paths below are relative to that same directory. Use whichever path applies to the tool that loaded this skill.

## Purpose

`queue` lets any agent — human or automated — add one or more URLs to `inbox.md`'s `## Pending` section **without fetching or ingesting them**. The human reviews the pending list and runs `/pin-llm-wiki run` (or `/pin-llm-wiki add <url>`) when ready to ingest.

Use `queue` when you discover a potentially relevant source mid-task and want to surface it for later review. Do not use `add` just to queue — `add` always fetches and ingests immediately.

---

## Guard

Check whether `.pin-llm-wiki.yml` exists in the current working directory. If not, stop:
> "No wiki found here (`.pin-llm-wiki.yml` missing). Run `/pin-llm-wiki init` to scaffold one first."

---

## Input

Accept one or more URLs from the invocation args (space-separated, or one per call). Each URL may be followed by inline tags:

- `<!-- detail:X -->` where X is `brief`, `standard`, or `deep`
- `<!-- branch:X -->` — GitHub only
- `<!-- clone -->` — GitHub only
- `<!-- skip -->` — queued but skipped on next `run`

An optional freeform **note** may follow the tags on the same line, wrapped in an HTML comment: `<!-- note: <text> -->`. This note is preserved as-is and ignored by all other subcommands.

---

## Per-URL logic

For each URL:

### 1. Check inbox.md

Read `inbox.md`.

- **URL already under `## Completed`:** skip this URL. Report:
  > "`<url>` already ingested (under ## Completed). To re-fetch, add `<!-- refresh -->` to its line."
- **URL already under `## Pending`:** skip this URL. Report:
  > "`<url>` already queued (under ## Pending)."
- **URL not in `inbox.md`:** proceed to step 2.

### 2. Append to `## Pending`

Append the line to the `## Pending` section of `inbox.md`, immediately before the `## Completed` heading (or at the end of the section):

```
- [ ] <url> <any inline tags> <any note tag>
```

Do not fetch, do not ingest, do not move to Completed.

### 3. Re-read before next URL

`inbox.md` was just mutated. Re-read it before processing the next URL to avoid duplicate appends.

---

## Confirmation

After processing all URLs, print:

```
Queued for ingest — <wiki-domain> wiki
<today>

  Added:    N URL(s)
  Skipped:  N (already pending or completed)

Next step: run `/pin-llm-wiki run` to ingest all pending items,
           or `/pin-llm-wiki add <url>` to ingest a single item immediately.
```

List each added URL on its own indented line under "Added:".
List each skipped URL with its reason under "Skipped:".

---

## Notes

- `queue` never runs a fetch, writes a raw file, or touches any wiki page.
- `queue` never runs `git commit` — see the wiki's `AGENTS.md` **Git — never auto-commit**.
- Any agent (human-directed or autonomous) may call `queue`. It is the only inbox mutation an agent may perform outside of the `add`, `run`, and `remove` workflows.
