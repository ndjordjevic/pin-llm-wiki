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

- **Claude Code:** use `/pin-llm-wiki` subcommands in the agent (`init`, `add`, `run [<url>]`, `lint`, `remove`, `queue`) — same as the skill’s `SKILL.md` dispatch table.
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
/pin-llm-wiki add https://example.com
```

Fetches, ingests, and writes `wiki/sources/<slug>.md`. Updates index, overview, log, and inbox in one shot.

For **web sources**, the skill automatically discovers the product's GitHub repo from the page content and fetches it as a companion. The result is a single unified source page (`wiki/sources/<domain>.md`) that covers the product website and the GitHub repo together — one inbox entry, one source page. Use `<!-- no-companion -->` to suppress this or `<!-- companion:github.com/<org>/<repo> -->` to override the discovered repo.

### Process pending inbox items

Edit `inbox.md` → add URLs under `## Pending` → then:

```
/pin-llm-wiki run              # process all pending items
/pin-llm-wiki run <url>        # process only this one URL from Pending
```

Ingests each pending URL in order, moves completed lines to `## Completed`. The single-URL form is useful when you want to ingest one specific source without touching the rest of the queue.

### Inline inbox tags

Append these (as HTML comments) to any URL line:

| Tag | Effect |
|---|---|
| `detail:brief` / `detail:standard` / `detail:deep` | Override detail level for this source |
| `branch:dev` | GitHub: use this branch instead of default |
| `clone` | GitHub deep: full `git clone` to `raw/github/<org>-<repo>/` |
| `skip` | Skip this URL on the next run |
| `companion:github.com/<org>/<repo>` | Web: skip GitHub discovery, use this repo as the companion |
| `no-companion` | Web: suppress companion GitHub fetch even if a repo is found |
| `note: text` | Freeform note for human review (queue only; ignored by ingest) |

Example:
```
- [ ] https://github.com/org/repo <!-- detail:deep --><!-- branch:dev -->
```

### Lint

```
/pin-llm-wiki lint
```

Runs 12 health checks (citation coverage, orphans, stale sources, frontmatter shape, split-product sources, etc.). Auto-fixes missing index links and re-syncs Cursor/Copilot adapter files.

### Queue a source (agent-friendly)

```
/pin-llm-wiki queue https://github.com/org/repo
```

Adds the URL to `inbox.md`'s `## Pending` section without fetching or ingesting. Useful for agents that discover interesting sources mid-task and want to surface them for human review. Multiple URLs accepted space-separated. Supports the same inline tags as `add` plus `<!-- note: text -->` for freeform rationale.

### Remove a source

```
/pin-llm-wiki remove <slug>
```

Soft-deletes to `wiki/.archive/`. Reports dangling references so you can fix them, then run lint for full wiki validation.

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
