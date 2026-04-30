# pin-llm-wiki

A multi-editor skill that automates the [Karpathy LLM Wiki pattern](https://x.com/karpathy/status/1805977730336702875): drop in URLs, get a local, citable, cross-referenced wiki that agents can read before answering.

**Where it runs:** [Claude Code](https://claude.com/product/claude-code) (slash commands), [GitHub Copilot](https://github.com/features/copilot) and [Cursor](https://cursor.com) (install the skill + follow the same workflows; see below).

## Why use it

`pin-llm-wiki` turns external sources into a durable knowledge base:

- `raw/` keeps immutable captures of the original sources.
- `wiki/` holds summarized, wikilinked pages with citations back to raw files.
- `AGENTS.md` tells AI agents to consult the wiki before answering domain questions.
- `inbox.md` gives humans and agents a simple queue for future sources.

The result is a repo-local memory layer: reviewable in git, queryable by agents, and less dependent on whatever context happens to fit in one chat.

## Install

From the directory where you want the skill (e.g. your wiki repo), run:

```bash
npx skills@latest add ndjordjevic/pin-llm-wiki
```

More options (agents, global scope, listing): [skills.sh](https://skills.sh) and `npx skills@latest --help`.

## Quickstart

Inside the repo that should become a wiki:

```bash
/pin-llm-wiki init
/pin-llm-wiki run https://github.com/org/repo
/pin-llm-wiki queue https://example.com
/pin-llm-wiki run
/pin-llm-wiki lint
```

After `init`, follow the generated wiki's `AGENTS.md`; it is the operating manual for agents working in that knowledge base.

## Commands

Use **`/pin-llm-wiki`** in the agent. Claude Code, Cursor, and GitHub Copilot all use the same `SKILL.md`.

| Subcommand | What it does |
|---|---|
| **`init`** | Scaffold `inbox.md`, `.pin-llm-wiki.yml`, `AGENTS.md`, `wiki/`, and `raw/` |
| **`run [url]`** | Ingest one URL, or omit `url` to process every pending item in `inbox.md` |
| **`queue <url> ...`** | Add URLs to `inbox.md` without fetching or ingesting |
| **`lint`** | Validate wiki health and apply light non-destructive fixes |
| **`remove <slug>`** | Soft-delete a source into `wiki/.archive/` |

Ingest rules, inbox HTML tags, companion repos, and multi-product deep mode live in `skills/pin-llm-wiki/SKILL.md` and its sibling workflow files.

## What gets created

```
inbox.md              source queue; drop URLs under ## Pending
.pin-llm-wiki.yml     config: domain, detail level, source types, lint cadence
AGENTS.md             canonical instructions for agents in the generated wiki
wiki/
  index.md            start here; full source list
  overview.md         rolling cross-source synthesis
  log.md              append-only ingest, refresh, and removal history
  sources/            one page per ingested source
  .archive/           soft-deleted sources
raw/
  github/             immutable GitHub repo captures
  youtube/            immutable YouTube transcripts + metadata
  web/                immutable web page captures
```

## Source types

| Type | Raw output | Notes |
|---|---|---|
| GitHub | `raw/github/<org>-<repo>.md` | Root repo URLs can include branch overrides and optional deep clones |
| YouTube | `raw/youtube/<video-id>-<slug>.md` | Transcript and metadata capture |
| Web | `raw/web/<slug>.md` | Web pages/sites, including GitHub non-root URLs |

GitHub non-root pages such as `https://github.com/org/repo/tree/main/docs` are treated as single-page web sources. Web sources can discover companion GitHub repos unless suppressed with `<!-- no-companion -->`.

With `<!-- detail:deep -->`, multi-product docs sites can produce one umbrella page plus one sub-page per product, all citing the same raw capture.

## Agent behavior

Generated wikis include `AGENTS.md`, which tells AI agents to:

- Read `wiki/index.md` before answering domain questions.
- Follow `[[wikilinks]]` into relevant source pages.
- Cite wiki page names in answers.
- Say when the wiki does not contain an answer, then fetch current information online.

Agents are also instructed not to run `git commit` or `git push` unless the human explicitly asks.

## Limits

This is a reviewable knowledge workflow, not an unattended publishing system. Generated pages should be inspected in git diffs. Large fetches have token guards, and Phase 1 lint defers contradiction and terminology-collision checks.
