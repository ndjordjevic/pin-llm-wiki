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
| `add <url>` | implemented |
| `run` | implemented |
| `lint` | implemented |
| `remove <slug>` | implemented |

## Dispatch

This SKILL.md lives inside the skill directory (e.g. `~/.claude/skills/pin-llm-wiki/`, `~/.copilot/skills/pin-llm-wiki/`, or `~/.cursor/skills/pin-llm-wiki/`, or the project-local `.claude/skills/`, `.copilot/skills/`, `.cursor/skills/` equivalents). All sibling files referenced below are in that same directory.

1. Identify the subcommand from the invocation args (the first word after `/pin-llm-wiki`).
2. Route — read the sibling file in this skill directory and follow its instructions exactly:
   - **`init`** → `init.md`
   - **`add`** → `add.md`
   - **`lint`** → `lint.md`
   - **`run`** → `run.md`
   - **`remove`** → `remove.md`
3. Do not proceed beyond this dispatch step before reading the target file.
