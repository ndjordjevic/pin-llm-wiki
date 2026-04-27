# pin-llm-wiki

A multi-editor skill that automates the [Karpathy LLM Wiki pattern](https://x.com/karpathy/status/1805977730336702875): drop a URL, get a citable, cross-referenced wiki page.

**Where it runs:** [Claude Code](https://claude.com/product/claude-code) (slash commands), [GitHub Copilot](https://github.com/features/copilot) and [Cursor](https://cursor.com) (install the skill + follow the same workflows; see below).

## Install

```bash
./install.sh           # symlinks to ~/.claude/skills/, ~/.copilot/skills/, ~/.cursor/skills/
./install.sh project   # symlinks to .claude/skills/, .copilot/skills/, .cursor/skills/ in cwd
./install.sh /path/to   # one explicit parent dir (creates /path/to/pin-llm-wiki → skill)
```

## Usage

- **Claude Code:** use `/pin-llm-wiki` subcommands in the agent (`init`, `add`, `run`, `lint`, `remove`) — same as the skill’s `SKILL.md` dispatch table.
- **Cursor / GitHub Copilot:** with this repo installed as a [Cursor skill](https://cursor.com/docs/context/skills) (see `~/.cursor/skills/` or `.cursor/skills/` from `./install.sh`) or a Copilot skill, the agent loads the same `SKILL.md`. In Cursor you can also type `/pin-llm-wiki` in Agent chat per Cursor’s skills UI. Alternatively, follow the step-by-step instructions in the generated `AGENTS.md` in your wiki. Each new wiki from `init` also gets `.cursor/rules/wiki-instructions.mdc` and `.github/copilot-instructions.md` so agents obey the pipeline even without a global skill install.
- **Git:** generated wikis instruct **all** agents not to run `git commit` / `git push` after ingests, lint, or other workflow steps unless you explicitly ask in chat—the human reviews diffs and commits.

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
