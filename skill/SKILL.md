---
name: pin-llm-wiki
description: "automate the LLM wiki pipeline: fetch → ingest → cite → lint a personal knowledge base"
trigger: /pin-llm-wiki
---

# /pin-llm-wiki

Automates Karpathy's LLM wiki pattern: drop URLs in `inbox.md`, the skill fetches, ingests, and maintains a cited, agent-readable knowledge base.

```
inbox.md (human drops URLs)
    ↓  fetch
raw/  (immutable source captures)
    ↓  ingest
wiki/  (LLM-maintained, cited, linked)
    ↓  lint
a healthy, queryable knowledge base
```

## Phase 1 subcommands

| Command | Status |
|---|---|
| `init` | implemented |
| `run [<url>]` | implemented (single-URL form auto-queues if URL is not already in inbox) |
| `lint` | implemented |
| `remove <slug>` | implemented |
| `queue <url> [<url> ...]` | implemented |

## Skill directory

This SKILL.md and all sibling files (`run.md`, `init.md`, `lint.md`, `remove.md`, `queue.md`, `ingest.md`, `templates/...`) live inside the skill directory: `~/.claude/skills/pin-llm-wiki/`, `~/.copilot/skills/pin-llm-wiki/`, `~/.cursor/skills/pin-llm-wiki/`, or the project-local `.claude/skills/` / `.copilot/skills/` / `.cursor/skills/` equivalents. All `templates/...` and sibling-file paths in this skill are relative to whichever skill directory the loading tool used.

## Dispatch

1. Identify the subcommand from the invocation args (the first word after `/pin-llm-wiki`).
2. Route — read the sibling file in this skill directory and follow its instructions exactly:
   - **`init`** → `init.md` (no Guard required — it scaffolds the wiki)
   - **`run`** → `run.md` (with or without a URL arg)
   - **`lint`** → `lint.md`
   - **`remove`** → `remove.md`
   - **`queue`** → `queue.md`
3. **Guard (every subcommand except `init`):** confirm `.pin-llm-wiki.yml` exists in the current working directory. If absent, stop with: *"No wiki found here (`.pin-llm-wiki.yml` missing). Run `/pin-llm-wiki init` to scaffold one first."* Subcommand files repeat this check by reference; you only need to enforce it once per invocation.
4. Do not proceed beyond this dispatch step before reading the target file.

## Git policy (canonical)

**Never run `git commit` or `git push` after any subcommand** — `init`, `run`, `ingest`, `refresh`, `lint`, `remove`, `queue`, or any auto-fix — unless the human explicitly asked to commit in this conversation. Subcommand files reference this policy without restating it. The wiki's own `AGENTS.md` carries the same rule for downstream agents.
