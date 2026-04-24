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

1. Identify the subcommand from the invocation args (the first word after `/pin-llm-wiki`).
2. Route:
   - **`init`** → Read `~/.claude/skills/pin-llm-wiki/init.md` and follow its instructions exactly.
   - **`add`** → Read `~/.claude/skills/pin-llm-wiki/add.md` and follow its instructions exactly.
   - **`lint`** → Read `~/.claude/skills/pin-llm-wiki/lint.md` and follow its instructions exactly.
   - **`run`** → Read `~/.claude/skills/pin-llm-wiki/run.md` and follow its instructions exactly.
   - **`remove`** → Read `~/.claude/skills/pin-llm-wiki/remove.md` and follow its instructions exactly.
3. Do not proceed beyond this dispatch step before reading the target file.
