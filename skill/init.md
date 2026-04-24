# init — scaffold a new wiki

## Guard

Before anything else:

1. Check whether `.pin-llm-wiki.yml` exists in the current working directory.
2. If it exists: **stop**. Tell the user:
   > "A wiki already exists here (`.pin-llm-wiki.yml` found). Use `/pin-llm-wiki add <url>` to ingest new sources or `/pin-llm-wiki run` to process pending inbox items."
3. Only proceed if `.pin-llm-wiki.yml` is absent.

---

## Interview

Conduct a 6-question interview, **one question at a time**. Present each question, wait for the answer, then proceed to the next. Do not batch questions.

Use `AskUserQuestion` if available (run `ToolSearch` with `query: "select:AskUserQuestion"` first to load its schema). If `AskUserQuestion` is not available, print each question clearly and wait for a user reply before continuing.

---

**Question 1 — Domain**

Ask:
> "What is this wiki about? (e.g. 'agentic AI frameworks', 'Rust async runtime', 'transformer architectures')"

Accept free text. Store as `DOMAIN`.

---

**Question 2 — Detail level**

First, display this table:

| Level | GitHub (per repo) | YouTube (per video) | Web (per domain) | Total (3 sources) | Notes |
|---|---|---|---|---|---|
| `brief` | ~15k tokens | ~10k tokens | ~5k tokens | ~30k | skeleton only |
| `standard` | ~30k tokens | ~40k tokens | ~22k tokens | ~90k (~$0.50–$2) | recommended |
| `deep` | ~100k+ tokens | ~40k tokens | ~80k+ tokens | ~200k+ ($5–$50+) | full crawl |

Then ask:
> "Which detail level? (`brief` / `standard` / `deep`)"
> Note: this sets the default for the wiki. Per-source overrides are available via `<!-- detail:X -->` tags in inbox.md.

Accept one of: `brief`, `standard`, `deep`. Store as `DETAIL_LEVEL`.

---

**Question 3 — Source types**

Ask:
> "Which source types will you use? Select all that apply: `web`, `github`, `youtube` (comma-separated, or type `all`)"

Normalize `all` → `['web', 'github', 'youtube']`. Validate each entry is one of the three. Store as `SOURCE_TYPES` (list).

---

**Question 4 — Git**

Ask:
> "Initialize a git repository? (yes/no, default: yes)"

Default: yes. Store as `GIT_INIT` (true/false).

If `GIT_INIT` is true, ask a follow-up:
> "Auto-commit after each ingest? (yes/no, default: no) — no means you review diffs before committing."

Default: no. Store as `AUTO_COMMIT` (true/false).

If `GIT_INIT` is false, set `AUTO_COMMIT = false`.

---

**Question 5 — Lint cadence**

Ask:
> "When should lint run?
>   `batch`       — once at the end of each `run` (recommended)
>   `per-ingest`  — after every single source ingest
>   `never`       — only when you explicitly run `/pin-llm-wiki lint`
>
> (default: batch)"

Accept one of: `batch`, `per-ingest`, `never`. Default: `batch`. Store as `AUTO_LINT`.

---

**Question 6 — Auto-mark complete**

Ask:
> "After ingesting a source, automatically flip its inbox line to `[x]`? (yes/no, default: yes)"

Default: yes. Store as `AUTO_MARK_COMPLETE` (true/false).

---

## Confirm

Print a summary:

```
Domain:         <DOMAIN>
Detail level:   <DETAIL_LEVEL>
Source types:   <SOURCE_TYPES joined by ", ">
Git init:       <GIT_INIT>  (auto-commit: <AUTO_COMMIT>)
Lint cadence:   <AUTO_LINT>
Auto-mark [x]:  <AUTO_MARK_COMPLETE>
```

Ask:
> "Proceed with scaffold? (yes/no)"

If the user says no: stop. If yes: continue to scaffold creation.

---

## Scaffold creation

Create all files in the current working directory. Create parent directories before children.

### Step 1 — Config file

Read `~/.claude/skills/pin-llm-wiki/templates/config.yml.tmpl`.
Substitute:
- `{{DOMAIN}}` → DOMAIN
- `{{DETAIL_LEVEL}}` → DETAIL_LEVEL
- `{{SOURCE_TYPES_LIST}}` → YAML list of selected types, e.g. `[web, github, youtube]`
- `{{AUTO_COMMIT}}` → AUTO_COMMIT as lowercase string (`true` or `false`)
- `{{AUTO_LINT}}` → AUTO_LINT
- `{{AUTO_MARK_COMPLETE}}` → AUTO_MARK_COMPLETE as lowercase string
- `{{CREATED_DATE}}` → today's date in YYYY-MM-DD format

Write result to `.pin-llm-wiki.yml`.

### Step 2 — Gitignore

Read `~/.claude/skills/pin-llm-wiki/templates/gitignore.tmpl`.
No substitutions.
Write to `.gitignore`.

### Step 3 — Inbox

Read `~/.claude/skills/pin-llm-wiki/templates/inbox.md.tmpl`.
No substitutions.
Write to `inbox.md`.

### Step 4 — Directory structure

Create these directories (use `mkdir -p` or equivalent, all at once):

Always:
- `raw/assets/`
- `wiki/sources/`
- `wiki/topics/`
- `wiki/syntheses/`
- `wiki/.archive/`

Conditionally:
- If `github` in SOURCE_TYPES: `raw/github/`
- If `youtube` in SOURCE_TYPES: `raw/youtube/`
- If `web` in SOURCE_TYPES: `raw/web/`

### Step 5 — Raw README files

Write `raw/README.md`. Build the file as follows:

Start with:
```
# raw/

Immutable source captures. Never edit these files manually; they are written by the fetch step.

## Directories

| Directory | Source type |
|---|---|
```

Then add exactly the rows that correspond to selected source types (do not include rows for unselected types):
- If `github` in SOURCE_TYPES: `| github/ | GitHub repo captures |`
- If `youtube` in SOURCE_TYPES: `| youtube/ | YouTube video transcripts + metadata |`
- If `web` in SOURCE_TYPES: `| web/ | Web page/site captures |`

Always add this final row:
```
| assets/ | Downloaded media and binary assets |
```

If `github` in SOURCE_TYPES: read `~/.claude/skills/pin-llm-wiki/templates/raw/github-README.md.tmpl` and write to `raw/github/README.md`.
If `youtube` in SOURCE_TYPES: read `~/.claude/skills/pin-llm-wiki/templates/raw/youtube-README.md.tmpl` and write to `raw/youtube/README.md`.
If `web` in SOURCE_TYPES: read `~/.claude/skills/pin-llm-wiki/templates/raw/web-README.md.tmpl` and write to `raw/web/README.md`.

### Step 6 — Wiki files

**`wiki/index.md`:**
Read `~/.claude/skills/pin-llm-wiki/templates/wiki/index.md.tmpl`.
Substitute `{{DOMAIN}}` and `{{CREATED_DATE}}`.
Write to `wiki/index.md`.

**`wiki/overview.md`:**
Read `~/.claude/skills/pin-llm-wiki/templates/wiki/overview.md.tmpl`.
Substitute `{{DOMAIN}}` and `{{CREATED_DATE}}`.
Write to `wiki/overview.md`.

**`wiki/log.md`:**
Read `~/.claude/skills/pin-llm-wiki/templates/wiki/log.md.tmpl`.
Substitute `{{DOMAIN}}` and `{{CREATED_DATE}}`.
Write to `wiki/log.md`.

Create empty placeholder files to preserve empty directories in git:
- `wiki/sources/.gitkeep`
- `wiki/topics/.gitkeep`
- `wiki/syntheses/.gitkeep`
- `wiki/.archive/.gitkeep`

### Step 7 — Generated CLAUDE.md

This is the most important file. It must be **fully self-contained** — a fresh Claude Code session in this repo must be able to run the full workflow from CLAUDE.md alone, without the skill installed.

Build CLAUDE.md in this order:

**7a.** Read `~/.claude/skills/pin-llm-wiki/templates/CLAUDE.md.tmpl`.
Substitute:
- `{{DOMAIN}}` → DOMAIN
- `{{DETAIL_LEVEL}}` → DETAIL_LEVEL
- `{{CREATED_DATE}}` → today's date
- `{{AUTO_COMMIT}}` → AUTO_COMMIT as lowercase string
- `{{AUTO_MARK_COMPLETE}}` → AUTO_MARK_COMPLETE as lowercase string

**7b.** Build the source protocol block to substitute for `{{SOURCE_PROTOCOLS}}`:

- If `github` in SOURCE_TYPES: read `~/.claude/skills/pin-llm-wiki/templates/protocols/github.md` and append to the block.
- If `youtube` in SOURCE_TYPES: read `~/.claude/skills/pin-llm-wiki/templates/protocols/youtube.md` and append to the block.
- If `web` in SOURCE_TYPES: read `~/.claude/skills/pin-llm-wiki/templates/protocols/web.md` and append to the block.

Replace `{{SOURCE_PROTOCOLS}}` in the template with this block.

**7c.** Write the fully-substituted content to `CLAUDE.md`.

### Step 8 — Git init (if GIT_INIT is true)

Run in order:
1. `git init`
2. `git add .pin-llm-wiki.yml .gitignore inbox.md CLAUDE.md raw/ wiki/`
3. `git commit -m "init: scaffold wiki for {{DOMAIN}}"`
   (substitute actual DOMAIN value in the commit message)

### Step 9 — Confirmation

Print:

```
Wiki scaffolded in <current directory>.

  .pin-llm-wiki.yml   config (domain, detail level, source types)
  inbox.md            drop URLs here under ## Pending
  CLAUDE.md           agent instructions — do not delete
  raw/                immutable source captures (written by fetch)
  wiki/               knowledge base (written by ingest)
    index.md          start here
    overview.md       rolling synthesis
    log.md            append-only history

Next: /pin-llm-wiki add <url>  (coming in the next phase)
Until then, sources can be ingested manually following the workflow in CLAUDE.md.
```
