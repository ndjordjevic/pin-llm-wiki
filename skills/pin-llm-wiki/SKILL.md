---
name: pin-llm-wiki
description: "Automates the Karpathy LLM Wiki workflow: turns web, GitHub, and YouTube URLs into well-structured, citable, wikilinked pages with automatic linting and sourcing — invoke with /pin-llm-wiki"
version: "1.0.0"
last_updated: "2026-04-30"

compatible_agents:
  tested:
    - claude
    - cursor
    - copilot
  untested:
    - codex

categories:
  - research
  - documentation
  - productivity

job_roles:
  - developer
  - researcher

author: "Nenad Djordjevic"
github: "ndjordjevic"
license: "apache-2.0"
trigger: "/pin-llm-wiki"
---

# /pin-llm-wiki

Automates Karpathy's LLM wiki pattern: drop URLs in `inbox.md`, the skill fetches, ingests, and maintains a cited, agent-readable knowledge base.

## Trigger phrases

- **`/pin-llm-wiki`** (with subcommands: `init`, `ingest`, `lint`, `queue`, `remove`)
- “Pin this YouTube video to my LLM wiki”
- “Ingest these research links into my wiki”
- “Run pin-llm-wiki lint on this knowledge base”
- “Queue these URLs, then batch-process the inbox”
- “Initialize a new Karpathy-style wiki with pin-llm-wiki”

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
| `ingest [<url>]` | implemented (single-URL form auto-queues if URL is not already in inbox) |
| `lint` | implemented |
| `remove <slug>` | implemented |
| `queue <url> [<url> ...]` | implemented |

## Skill directory

This SKILL.md and all sibling files (`ingest.md`, `init.md`, `lint.md`, `remove.md`, `queue.md`, `ingest-protocol.md`, `templates/...`) live inside the skill directory: `~/.claude/skills/pin-llm-wiki/`, `~/.copilot/skills/pin-llm-wiki/`, `~/.cursor/skills/pin-llm-wiki/`, or the project-local `.claude/skills/` / `.copilot/skills/` / `.cursor/skills/` equivalents. In this repository the canonical copy is **`skills/pin-llm-wiki/`**. All `templates/...` and sibling-file paths in this skill are relative to whichever skill directory the loading tool used.

## Dispatch

1. Identify the subcommand from the invocation args (the first word after `/pin-llm-wiki`).
2. Route — read the sibling file in this skill directory and follow its instructions exactly:
   - **`init`** → `init.md` (no Guard required — it scaffolds the wiki)
   - **`ingest`** → `ingest.md` (with or without a URL arg)
   - **`lint`** → `lint.md`
   - **`remove`** → `remove.md`
   - **`queue`** → `queue.md`
3. **Guard (every subcommand except `init`):** confirm `.pin-llm-wiki.yml` exists in the current working directory. If absent, stop with: *"No wiki found here (`.pin-llm-wiki.yml` missing). Run `/pin-llm-wiki init` to scaffold one first."* Subcommand files repeat this check by reference; you only need to enforce it once per invocation.
4. Do not proceed beyond this dispatch step before reading the target file.

## Git policy (canonical)

**Never run `git commit` or `git push` after any subcommand** — `init`, `ingest`, `refresh`, `lint`, `remove`, `queue`, or any auto-fix — unless the human explicitly asked to commit in this conversation. Subcommand files reference this policy without restating it. The wiki's own `AGENTS.md` carries the same rule for downstream agents.
