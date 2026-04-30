# init — scaffold a new wiki

(Skill-directory paths are defined in `SKILL.md`.)

## Guard (inverse: must NOT already exist)

If `.pin-llm-wiki.yml` exists in the current working directory, **stop**: *"A wiki already exists here (`.pin-llm-wiki.yml` found). Use `/pin-llm-wiki run <url>` to ingest a new source or `/pin-llm-wiki run` to process pending inbox items."* Only proceed if absent.

---

## Interview

Conduct a 6-question interview, **one question at a time**. Present each question, wait for the answer, then proceed to the next. Do not batch questions.

Use the environment's dedicated user-question tool if available (for example, Copilot's `ask_user`). If no such tool is available, print each question clearly and wait for a user reply before continuing.

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
| `deep` | ~100k+ tokens | ~40k tokens | ~80k+ tokens | ~200k+ ($5–$50+) | docs-driven crawl; multi-product platforms (≥2 products) produce one umbrella + per-product sub-pages, all citing one raw file |

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
Git init:       <GIT_INIT>
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

Read `<skill-dir>/templates/config.yml.tmpl`.
Substitute:
- `{{DOMAIN}}` → DOMAIN
- `{{DETAIL_LEVEL}}` → DETAIL_LEVEL
- `{{SOURCE_TYPES_LIST}}` → YAML list of selected types, e.g. `[web, github, youtube]`
- `{{AUTO_LINT}}` → AUTO_LINT
- `{{AUTO_MARK_COMPLETE}}` → AUTO_MARK_COMPLETE as lowercase string
- `{{CREATED_DATE}}` → today's date in YYYY-MM-DD format

Write result to `.pin-llm-wiki.yml`.

### Step 2 — Gitignore

Read `<skill-dir>/templates/gitignore.tmpl`.
No substitutions.
Write to `.gitignore`.

### Step 3 — Inbox

Read `<skill-dir>/templates/inbox.md.tmpl`.
No substitutions.
Write to `inbox.md`.

### Step 4 — Directory structure

Create these directories (use `mkdir -p` or equivalent, all at once):

Always:
- `raw/assets/`
- `wiki/sources/`
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

If `github` in SOURCE_TYPES: read `<skill-dir>/templates/raw/github-README.md.tmpl` and write to `raw/github/README.md`.
If `youtube` in SOURCE_TYPES: read `<skill-dir>/templates/raw/youtube-README.md.tmpl` and write to `raw/youtube/README.md`.
If `web` in SOURCE_TYPES: read `<skill-dir>/templates/raw/web-README.md.tmpl` and write to `raw/web/README.md`.

### Step 6 — Wiki files

**`wiki/index.md`:**
Read `<skill-dir>/templates/wiki/index.md.tmpl`.
Substitute `{{DOMAIN}}` and `{{CREATED_DATE}}`.
Write to `wiki/index.md`.

**`wiki/overview.md`:**
Read `<skill-dir>/templates/wiki/overview.md.tmpl`.
Substitute `{{DOMAIN}}` and `{{CREATED_DATE}}`.
Write to `wiki/overview.md`.

**`wiki/log.md`:**
Read `<skill-dir>/templates/wiki/log.md.tmpl`.
Substitute `{{DOMAIN}}` and `{{CREATED_DATE}}`.
Write to `wiki/log.md`.

Create empty placeholder files to preserve empty directories in git:
- `wiki/sources/.gitkeep`
- `wiki/.archive/.gitkeep`

### Step 6a — Wiki README

Read `<skill-dir>/templates/README.md.tmpl`.
Substitute `{{DOMAIN}}` → DOMAIN.
Write result to `README.md`.

### Step 7 — Agent instruction files

Several files are written from the same **AGENTS_BODY** so that Claude Code, GitHub Copilot, and Cursor all behave identically in this wiki (`AGENTS.md` plus one adapter file per tool below).

**7a. Assemble AGENTS_BODY** (canonical content, used by all three files below):

Read `<skill-dir>/templates/AGENTS.md.tmpl`.
Substitute:
- `{{DOMAIN}}` → DOMAIN
- `{{DETAIL_LEVEL}}` → DETAIL_LEVEL
- `{{CREATED_DATE}}` → today's date
- `{{AUTO_MARK_COMPLETE}}` → AUTO_MARK_COMPLETE as lowercase string

Build the source protocol block to substitute for `{{SOURCE_PROTOCOLS}}`:
- If `github` in SOURCE_TYPES: read `<skill-dir>/templates/protocols/github.md` and append.
- If `youtube` in SOURCE_TYPES: read `<skill-dir>/templates/protocols/youtube.md` and append.
- If `web` in SOURCE_TYPES: read `<skill-dir>/templates/protocols/web.md` and append.

Replace `{{SOURCE_PROTOCOLS}}` with the assembled block.
Hold the fully-substituted result in memory as **AGENTS_BODY**.

**7b. Write `AGENTS.md`** — the universal agent operating manual (read by Copilot, Cursor, Claude Code, and 20+ other tools):

Write AGENTS_BODY to `AGENTS.md`.

**7c. Write `CLAUDE.md`** — thin Claude Code adapter:

Read `<skill-dir>/templates/CLAUDE.md.tmpl`.
Substitute `{{DOMAIN}}` → DOMAIN.
Write to `CLAUDE.md`.
(This file contains `@AGENTS.md` — Claude Code expands it at load time.)

### Step 8 — Git init (if GIT_INIT is true)

Run `git init` only. Do not run `git add` or `git commit` (see SKILL.md Git policy).

### Step 9 — Confirmation

Print:

```
Wiki scaffolded in <current directory>.

  .pin-llm-wiki.yml                           config (domain, detail level, source types)
  README.md                                   human-facing usage guide for this wiki
  inbox.md                                    drop URLs here under ## Pending
  AGENTS.md                                   agent instructions — canonical (Claude Code, Cursor, GitHub Copilot, Copilot CLI)
  CLAUDE.md                                   agent instructions — Claude Code adapter
  raw/                                        immutable source captures (written by fetch)
  wiki/                                       knowledge base (written by ingest)
    index.md                                  start here
    overview.md                               rolling cross-source overview
    log.md                                    append-only history

Next: /pin-llm-wiki run <url>

Note: AGENTS.md is the single source of truth — all major AI tools (Claude Code,
Cursor, GitHub Copilot, Copilot CLI) load it automatically.
```
