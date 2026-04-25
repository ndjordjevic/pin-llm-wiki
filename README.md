# pin-llm-wiki

A Claude Code skill that automates the [Karpathy LLM Wiki pattern](https://x.com/karpathy/status/1805977730336702875): drop a URL, get a citable, cross-referenced wiki page.

## Install

```bash
./install.sh           # installs to ~/.claude/skills/ as a symlink
./install.sh project   # installs to .claude/skills/ in current directory
```

## Usage

All commands are run inside a Claude Code session.

### Start a new wiki

```
/pin-llm-wiki init
```

Runs a short interview (domain, detail level, source types, git settings), then scaffolds `inbox.md`, `wiki/`, `raw/`, `AGENTS.md`, and `.pin-llm-wiki.yml` in the current directory.

### Add a single source

```
/pin-llm-wiki add https://github.com/org/repo
```

Fetches, ingests, and writes `wiki/sources/<slug>.md`. Updates index, overview, log, and inbox in one shot.

### Process all pending inbox items

Edit `inbox.md` → add URLs under `## Pending` → then:

```
/pin-llm-wiki run
```

Ingests each pending URL in order, moves completed lines to `## Completed`.

### Inline inbox tags

Append these (as HTML comments) to any URL line:

| Tag | Effect |
|---|---|
| `detail:brief` / `detail:standard` / `detail:deep` | Override detail level for this source |
| `branch:dev` | GitHub: use this branch instead of default |
| `clone` | GitHub deep: full `git clone` to `raw/github/<org>-<repo>/` |
| `skip` | Skip this URL on the next run |

Example:
```
- [ ] https://github.com/org/repo <!-- detail:deep --><!-- branch:dev -->
```

### Lint

```
/pin-llm-wiki lint
```

Runs 10 health checks (citation coverage, orphans, stale sources, frontmatter shape, etc.). Auto-fixes missing index links and creates topic stubs for concepts appearing in 2+ sources.

### Remove a source

```
/pin-llm-wiki remove <slug>
```

Soft-deletes to `wiki/.archive/`. Runs lint to surface orphaned wikilinks.

### Refresh a source

Add `<!-- refresh -->` to its line in `## Completed`, then run `/pin-llm-wiki run`.

## Wiki structure

```
inbox.md              drop URLs here
.pin-llm-wiki.yml     config
wiki/
  index.md            start here
  overview.md         rolling synthesis
  log.md              append-only history
  sources/            one page per ingested source
  topics/             cross-source concept pages (created at lint time)
  syntheses/          deep-dive documents (manual)
  .archive/           soft-deleted sources
raw/
  github/             immutable GitHub repo captures
  youtube/            immutable YouTube transcripts + metadata
  web/                immutable web page captures
```

## Source types

| Type | Fetch tool | Raw output |
|---|---|---|
| GitHub | `gh` CLI | `raw/github/<org>-<repo>.md` |
| YouTube | `yt-dlp` | `raw/youtube/<video-id>-<slug>.md` |
| Web | `WebFetch` | `raw/web/<domain>.md` |
