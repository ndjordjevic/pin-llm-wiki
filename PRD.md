# pin-llm-wiki — Product Requirements Document

**Date:** 2026-04-23
**Status:** Draft 1 — post-manual-pass
**Phase:** 1 (Skills-only MVP)
**Inputs:** `research.md`, `manual-pass-plan.md`, `manual-pass-findings.md`

---

## 1. Problem & vision

### The problem

Karpathy's LLM Wiki pattern — a curated, cited, agent-readable markdown knowledge base — is powerful but fully manual: hand-clipped sources, hand-written CLAUDE.md, hand-invoked ingest. It works for one motivated user on one domain; it does not generalize, doesn't scale, and doesn't survive handoff.

### The vision

**pin-llm-wiki** is a reusable Claude Code skill that automates the pipeline:

```
inbox.md (human drops URLs)
    ↓  fetch
raw/  (immutable source capture)
    ↓  ingest
wiki/  (LLM-maintained, cited, linked)
    ↓  lint (batched at end of run)
a healthy, queryable knowledge base
```

The human's job shrinks to **drop URLs → review output**. Everything else is agent-driven.

### Load-bearing principles (validated in manual pass — do not revisit)

1. **Citations first.** Every factual claim cites its raw file. No citation → no claim. Linter enforces.
2. **Raw is immutable.** Never edited, never auto-deleted.
3. **Inbox is human-owned.** Agent marks/moves `[x]`, never adds or removes URLs.
4. **Git is the versioning layer.** The wiki is a git repo. Rollback always possible.
5. **The wiki is for both humans and agents.** Generated `CLAUDE.md` instructs future agents to read `wiki/index.md` first. Without that, the wiki is inert.

---

## 2. Goals & non-goals

### Phase 1 goals

- `/pin-llm-wiki init` — conversational interview produces a working, scaffolded wiki repo.
- `/pin-llm-wiki add <url>` — one-shot fetch + ingest for a single URL.
- `/pin-llm-wiki run` — batch process all pending inbox URLs.
- `/pin-llm-wiki lint` — report-only lint pass.
- Three source types supported at ship: `github`, `youtube`, `web`.
- Three detail levels: `brief` / `standard` / `deep` (locked at init).
- Zero hallucinations in the output — measured by manual citation spot-check on a test wiki.
- Fresh-agent consumption test passes: a new Claude Code session answers cross-source questions from the wiki without training-data drift.

### Non-goals for Phase 1 (deferred)

- Python CLI (`pip install pin-llm-wiki`) — Phase 2.
- MCP server — Phase 3.
- Obsidian plugin / rendering polish — Phase 4.
- Additional source types (arxiv, PDFs, Substack, Twitter/X, *.github.io, etc.) — post-MVP.
- Multi-user / team collaboration.
- Auth-gated sources (internal docs behind SSO).
- Budget / cost-cap enforcement.
- Automatic topic-page *content* generation (stub creation only).
- Formal `/pin-llm-wiki harvest` command (manual for now).
- Multi-LLM backend (Claude-only for MVP; abstract later).

---

## 3. Users & use cases

### Primary user

A solo learner / researcher / engineer building a personal knowledge base on a chosen domain (e.g. agentic AI, a new programming language, a research area). Technical enough to run Claude Code; not technical enough to want to hand-craft CLAUDE.md for every new wiki.

### Secondary user

A small team (≤5) sharing a domain-focused wiki via git — same repo, same skill, multiple humans dropping URLs.

### Core use cases

| # | Use case | Commands involved |
|---|---|---|
| 1 | Start a new wiki from scratch | `init` |
| 2 | Add a single source I just found | `add <url>` |
| 3 | Drop N URLs and process them as a batch | edit `inbox.md`, then `run` |
| 4 | Re-fetch a source that updated upstream | add `<!-- refresh -->` tag, `run` |
| 5 | Remove a source I no longer trust | `remove <slug>` |
| 6 | Check wiki health | `lint` |
| 7 | Ask the wiki a question (via a coding agent) | Any Claude Code session; CLAUDE.md makes the agent read the wiki |

---

## 4. Functional requirements

### 4.1 `init` — scaffold a new wiki

**Trigger:** `/pin-llm-wiki init` in an empty directory (or a directory without `.pin-llm-wiki.yml`).

**Behavior:** Conversational interview — one question at a time:

1. **Domain:** "What is this wiki about?" (free text)
2. **Detail level:** `brief` / `standard` / `deep` — show estimated token cost per typical source at each level; note detail is locked post-init.
3. **Source types:** multi-select from `[web, github, youtube]` (more types post-MVP).
4. **Git:** initialize repo? (default yes.) Auto-commit each ingest? (default no — validated as the right default in manual pass; per-step human review beats surprise commits.)
5. **Lint cadence:** `batch` (end of `run`) / `per-ingest` / `manual only`. Default `batch`.
6. **Auto-mark inbox `[x]` after ingest:** default yes.

**Generated artifacts:**

```
<wiki>/
  .git/                           (if git enabled)
  .pin-llm-wiki.yml               (config from interview)
  .gitignore                      (raw/github/*/clones, .DS_Store, etc.)
  inbox.md                        (# Inbox / ## Pending / ## Completed)
  CLAUDE.md                       (load-bearing agent instructions — see §4.7)
  raw/
    README.md
    web/README.md                 (if web selected)
    github/README.md              (if github selected)
    youtube/README.md             (if youtube selected)
    assets/
  wiki/
    index.md                      (must link to overview.md and log.md)
    log.md
    overview.md
    sources/
    topics/
    syntheses/
```

**Config schema (`.pin-llm-wiki.yml`):**

```yaml
version: 1
created: 2026-04-23
domain: "..."
detail_level: brief | standard | deep
source_types: [web, github, youtube]
auto_commit: false
auto_lint: batch            # never | batch | per-ingest
auto_mark_complete: true
stale_threshold_days: 30    # configurable per §4.5 lint check
```

### 4.2 `add <url>` — single-source ingest

**Trigger:** `/pin-llm-wiki add <url>`

**Behavior:**
1. Append URL to `inbox.md` under `## Pending` (unless already present).
2. Detect source type from URL (see §4.4).
3. Fetch per type.
4. Ingest (see §4.6).
5. Move inbox line to `## Completed`, flip `[ ]` → `[x]`, append `<!-- ingested YYYY-MM-DD -->`.
6. If `auto_commit: true`: `git commit -m "ingest: <slug>"`.
7. No lint unless `auto_lint: per-ingest`.

### 4.3 `run` — batch process pending inbox

**Trigger:** `/pin-llm-wiki run`

**Behavior:**
1. Read `inbox.md`. For each unchecked line under `## Pending`:
   - Honor tags (`<!-- skip -->`, `<!-- refresh -->`, `<!-- detail:X -->`, `<!-- branch:X -->`, `<!-- clone -->`).
   - Detect type, fetch, ingest, move to `## Completed`.
2. At the end: run `lint` once (if `auto_lint: batch`).
3. If `auto_commit: true`: commit per-source (so diffs are reviewable).

**Idempotency:** if `run` crashes at source 4 of 7:
- Sources 1–3 remain in `## Completed`.
- Source 4 may have partial `raw/` content — detectable by hash/size; discarded and refetched.
- Re-running `run` picks up from the first item still under `## Pending`.

**Guard rail:** if any single source exceeds 200k input tokens during fetch, halt and surface to user. Cost-cap is out of scope for MVP but this guard prevents runaway detail:deep fetches.

### 4.4 Fetch per source type

**Source type detection (inbox URL → type):**

| URL pattern | Type | Tool |
|---|---|---|
| `github.com/<org>/<repo>` | github | `gh` CLI |
| `youtube.com/watch?v=` or `youtu.be/` | youtube | `yt-dlp` |
| anything else | web | `WebFetch` |

**GitHub fetch protocol** (validated in manual pass):

1. `gh repo view <org>/<repo> --json name,description,url,homepageUrl,stargazerCount,forkCount,pushedAt,primaryLanguage,licenseInfo,defaultBranchRef` — capture metadata and default branch.
2. `gh release list --repo <org>/<repo> --limit 1` — capture latest release tag.
3. `gh api repos/<org>/<repo>/readme` — decode base64, full README.
4. `gh api repos/<org>/<repo>/contents/` — top-level structure.
5. If `docs/` exists: list + fetch key files (guides, architecture, testing).
6. If `examples/` exists: list only.
7. Skim other folders; annotate important ones (source/lib, plugin manifests, tests, agent instruction files `CLAUDE.md` / `AGENTS.md` / `GEMINI.md`); skip boilerplate.
8. Save to `raw/github/<org>-<repo>.md` (one compiled file). Update `raw/github/README.md` row.
9. Use `defaultBranchRef.name` unless `<!-- branch:X -->` override present. Never assume `main`.
10. At deep detail with `<!-- clone -->`: `git clone` to `raw/github/<org>-<repo>/` (gitignored).

**YouTube fetch protocol** (validated):

1. `yt-dlp --dump-json <url>` — description, chapters, title, channel, duration, upload date. One call.
2. `yt-dlp --write-auto-sub --sub-format vtt --skip-download --sub-lang en-orig <url>` — transcript. Prefer `en-orig` over `en`.
3. Parse VTT: rolling-caption format (each cue has 2 lines, last is live word-by-word). Take the first clean line per cue (no `<c>` tags), deduplicate consecutive duplicates, group by chapter heading (from `--dump-json`).
4. Save to `raw/youtube/<video-id>-<slug>.md` with sections: metadata, description, chapter list, transcript grouped by chapter.
5. Fallback: if no transcript track, flag inbox line `<!-- fetch-failed:no-transcript -->` and skip (do not mark `[x]`).

**Web fetch protocol** (validated):

1. **Check `<domain>/llms.txt` first.** If present, one fetch yields a structured concept index — often replaces the crawl.
2. If no llms.txt, fetch landing page + discover docs via `/docs`, `/documentation`, `/guide`, `sitemap.xml`.
3. Depth by detail level:
   - `brief`: landing only.
   - `standard`: llms.txt (if any) + landing + docs index + ~4–10 key pages (e.g. per-product overviews).
   - `deep`: full crawl within domain.
4. Follow redirects; log the *final* URL to the raw file (not the original — stale domains silently redirect).
5. Save to `raw/web/<domain>.md` (one compiled file at brief/standard). At deep, use `raw/web/<domain>/<page-slug>.md` per-page.
6. Respect `robots.txt`; set user agent; rate-limit.
7. Use `WebFetch` as default. Only fall back to Jina Reader (`r.jina.ai/<url>`) or headless browser if WebFetch returns a content-free skeleton on a specific site.

### 4.5 Lint

**Trigger:** `/pin-llm-wiki lint`, or end of `run` when `auto_lint: batch`.

**Checks** (validated in manual pass):

| # | Check | Severity |
|---|---|---|
| 1 | Citation coverage — every factual claim has a chain to a raw file | ERROR |
| 2 | Contradictions — conflicting claims across pages; rank by source authority | WARN |
| 3 | Orphans — pages with no inbound `[[wikilinks]]`; **includes `overview.md` and `log.md`** | WARN |
| 4 | Data gaps — concepts named in ≥2 source pages with no topic page | INFO (suggests topic creation) |
| 5 | Missing cross-references — page mentions a wiki-known entity without linking; empty `related:` when cross-refs are warranted | WARN |
| 6 | Stale sources — last refresh > `stale_threshold_days` (default 30) | INFO |
| 7 | Terminology collisions — same term used for different concepts across sources (e.g. "skills" in Superpowers vs DeepAgents) | WARN |
| 8 | Frontmatter shape — source pages must NOT include `sources:`; topic/synthesis pages may | ERROR |
| 9 | Citation path format — wiki-to-raw links must be relative-from-file (`../../raw/...` from `wiki/sources/`) | ERROR |

**Output:** structured report (counts by severity, list of findings with file:line references). Report only — no auto-fix in MVP, with two exceptions:

- **Auto-fixable:** missing `overview.md` / `log.md` links in `index.md` scaffold.
- **Auto-fixable (stub only):** topic pages for concepts with ≥2-source coverage — generate scaffold with frontmatter + banner citations, leave body for human or next `add` to fill.

### 4.6 Ingest

**Input:** a completed fetch (raw file ready in `raw/`).

**Output:** updated `wiki/sources/<slug>.md`, updated `wiki/index.md`, updated `wiki/overview.md`, appended entry in `wiki/log.md`, appended row in `raw/<type>/README.md`, moved inbox line.

**Ingest behavior:**

1. Read the raw file.
2. Create or update `wiki/sources/<slug>.md`:
   - Frontmatter: `type: source`, tags, `related: []` (resolved at lint time), `detail_level` from config, `created` / `updated`.
   - **No `sources:` field** (source pages don't cite themselves).
   - Body: summary paragraph, banner citation (`_All claims below are sourced from ../../raw/.../file.md unless otherwise noted._`), then sectioned content. Per-type templates:
     - **GitHub:** what it does, installation, key features, architecture, example usage, maintenance status.
     - **YouTube:** what the video is about (1 paragraph — "replace watching" bar), key points by chapter, notable quotes, speaker context.
     - **Web/product:** what it does, key features, architecture/concepts, main APIs, when to use, ecosystem.
3. **Do not create topic pages.** Topic creation is a lint-time action — see §4.5 check #4.
4. Update `wiki/index.md`: add source row, increment count.
5. Update `wiki/overview.md`: extend the current synthesis to reflect the new source. Overview cites `[[source pages]]`, not raw files.
6. Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | <source> | <one-line summary>` followed by bullet list of files touched.
7. Append row to `raw/<type>/README.md`.
8. Move inbox line: `## Pending` → `## Completed`, `[ ]` → `[x]`, append `<!-- ingested YYYY-MM-DD -->`.
9. If `auto_commit: true`: `git commit -m "ingest: <slug>"`.

**Merge rules (when updating an existing topic page, created by a prior lint run):**

- Add new facts; do not duplicate.
- Conflict: insert a `> **Conflict:**` block citing both sources. Do not silently overwrite. Source authority: official docs > GitHub README > YouTube (official channel) > blogs / secondary.

### 4.7 Generated CLAUDE.md

The single most load-bearing artifact of the whole system. Every generated CLAUDE.md must include:

```markdown
## For AI agents working in this repo

Before answering any question about this wiki's domain, you MUST:
1. Read `wiki/index.md` to identify relevant pages.
2. Follow `[[wikilinks]]` to drill into relevant pages.
3. Cite wiki page names in your answer.
4. If the answer is not in the wiki, say so clearly — do not infer from training data.
```

Plus the full protocol for each source type the user selected (GitHub / YouTube / Web fetch protocols from §4.4, ingest workflow from §4.6, citation rules, frontmatter rules). The `agentic-ai-wiki/CLAUDE.md` at the end of the manual pass is the reference implementation.

### 4.8 Remove

`/pin-llm-wiki remove <slug>`:
1. Soft-delete by default: move `raw/<type>/<slug>*` and `wiki/sources/<slug>.md` to `wiki/.archive/` (configurable).
2. Run lint immediately: flag orphaned `[[wikilinks]]` and sentences citing the removed raw file.
3. Report to user; do not auto-rewrite.

### 4.9 Refresh

Inbox tag: `- [x] https://... <!-- refresh -->`:
1. Fetch agent re-fetches.
2. Hash the cleaned raw content; compare to existing.
3. If differs: update raw file, re-run ingest (wiki pages updated, not duplicated), append log entry `refresh: <slug>`.
4. If identical: log `refresh: <slug> (no change)`, do nothing else.

---

## 5. Technical design

### 5.1 Packaging (Phase 1)

- Skill at `~/.claude/skills/pin-llm-wiki/SKILL.md` plus supporting `.md` files per subcommand.
- Triggered by `/pin-llm-wiki <subcommand>` in any Claude Code session.
- Generated wiki repos are self-contained — their CLAUDE.md loads the workflow into any fresh agent session in that repo.

### 5.2 Agent architecture

**One ingest agent, branches by source type** (validated as simpler than the earlier FetchOrchestrator idea):

- Main skill dispatches to subcommand handlers (init, add, run, lint, refresh, remove).
- Each subcommand is a prose workflow in the skill, invoked in the Claude Code session (no subagents required for MVP).
- Subagents (`Agent` tool, `subagent_type=Explore`) only when needed for large crawls or context pressure at deep detail.

### 5.3 Directory conventions (validated)

- Raw: one compiled file per source at brief/standard.
  - `raw/github/<org>-<repo>.md`
  - `raw/youtube/<video-id>-<slug>.md`
  - `raw/web/<domain>.md`
- Raw README per type: `raw/<type>/README.md` table with `File | Source | Fetched | Notes` (github adds `Stars`).
- Wiki source pages: `wiki/sources/<slug>.md`.
- Wiki topic pages: `wiki/topics/<slug>.md` (created at lint time).
- Wiki synthesis pages: `wiki/syntheses/<slug>.md` (manual, user-driven).

### 5.4 Citation & frontmatter rules (validated, enforced by lint)

- Source pages: no `sources:` frontmatter; banner citation from a single raw file; per-paragraph citations only when a second raw file is incorporated.
- Topic pages: `sources:` lists contributing source pages as wikilinks; inline citations to raw files.
- Synthesis / overview pages: cite `[[source pages]]`, not raw files directly.
- Paths: always relative-from-file (`../../raw/...` from `wiki/sources/`).
- Obsidian compatibility: list-form wikilinks (`- "[[page]]"`), not inline bracket arrays.

### 5.5 Cost & token profile (measured in manual pass)

| Source type | Fetch | Ingest | Total | Notes |
|---|---|---|---|---|
| GitHub (standard) | ~20k in | ~8k in | ~28k | README + docs |
| YouTube (standard) | ~1k (CLI) | ~40k in | ~40k | transcript-heavy |
| Web (standard) | ~13k in | ~9k in | ~22k | docs site with llms.txt — cheapest |
| Full pass (3 sources) | | | ~98k | well under 200k guard rail |

At current Anthropic rates: standard pass of 3–10 sources ≈ $0.50–$5. Deep detail on a large source: 200k–2M tokens, $10–$50. Init interview surfaces this.

---

## 6. Acceptance criteria

### 6.1 `init` produces a working wiki

- Running `init` in an empty folder creates the full scaffold in §4.1.
- Generated `CLAUDE.md` loads workflow into a fresh Claude Code session with no extra setup.
- A fresh Claude Code session, pointed at the generated wiki, understands the workflow and can run `add <url>` without hand-holding.

### 6.2 Each source type ingests cleanly

- For each of `github`, `youtube`, `web`:
  - Raw file created at the correct path with expected sections.
  - Wiki source page created with correct frontmatter (no `sources:`), banner citation, sectioned body.
  - `raw/<type>/README.md` updated.
  - `wiki/index.md` updated (count + sources table row).
  - `wiki/overview.md` updated to incorporate new source.
  - `wiki/log.md` appended.
  - Inbox line *moved* from Pending to Completed with ingested date comment.

### 6.3 Lint catches the bugs from manual pass

The MVP lint must catch:
- Source page with `sources:` frontmatter set.
- Citation path that's root-relative instead of relative-from-file.
- Inbox line marked `[x]` but still under `## Pending`.
- `overview.md` / `log.md` not linked from `index.md`.
- Source page with no inbound wikilink (orphan).
- Page with factual claim lacking citation chain.

### 6.4 Agent-consumption test passes

On a test wiki with ≥3 sources, a fresh Claude Code session asked a cross-source question:
- Reads `wiki/index.md` first (evidence: visible tool calls).
- Cites `[[wikilinks]]` in the answer.
- Synthesizes from wiki content only, no hallucinated facts.

Measured via spot-check on the answer against the wiki.

### 6.5 Idempotency

- `run` can be interrupted at any point and re-run. No duplicate ingests; no half-completed raw files linger. Manual test: kill `run` after source 2 of 5 succeeds, re-invoke `run`, confirm sources 3–5 process and 1–2 are skipped.

### 6.6 Zero hallucinations

Manual spot-check on 10 random factual claims across a 3-source test wiki: every claim maps back to specific text in the cited raw file. Zero tolerance.

---

## 7. Open questions deferred to implementation

These don't block PRD sign-off but will need a decision during build:

1. **Lint auto-fix scope.** Should topic stub creation (Check #4 auto-fix) run automatically at lint time, or only when user passes `--fix`? Lean: `--fix` flag required.
2. **Overview.md citation enforcement.** Currently overview has no citations; Check #1 allows `[[source page]]` wikilinks as citations. Should `overview.md` be required to have them? Lean: yes, but warning-level not error.
3. **Deep-detail raw layout.** Flat compiled file vs per-page directory. Lean: per-page directory at deep, flat compiled file at brief/standard.
4. **Harvest command.** `/pin-llm-wiki harvest` — formalize the "agent-consumption output → topic page" workflow in MVP or defer? Lean: defer; document the manual version in generated CLAUDE.md.
5. **Cost-cap / budget guard.** Out of MVP scope per §2 non-goals, but should `init` prompt for a soft ceiling? Lean: no — 200k-per-source guard rail in §4.3 is enough for MVP.
6. **Multi-LLM abstraction.** MVP is Claude-only (skills live in Claude Code). Abstraction layer deferred to Phase 2 CLI.
7. **VTT vs SRT fallback.** SRT is cleaner than rolling-caption VTT. Should ingest prefer `--sub-format srt` when available? Lean: yes, with VTT fallback.

---

## 8. Out of scope (explicitly deferred)

- Python CLI packaging (Phase 2).
- MCP server (Phase 3).
- Additional source types beyond web/github/youtube.
- Auth-gated source fetching (internal docs, SSO sites).
- Team / multi-user collaboration features beyond vanilla git.
- Real-time / streaming ingest (watch a YouTube channel, auto-ingest new videos).
- Rendering UI / Obsidian plugin.
- Localization / non-English content handling.
- Budget / cost-cap enforcement.
- LLM-backend abstraction.

---

## 9. Next steps

1. **Sign off this PRD** with any scope adjustments.
2. Write the skill — start with `init` (lowest risk, highest UX value).
3. Then `add` for each source type in order of manual-pass-validated complexity: GitHub first, YouTube second, Web third.
4. Implement `lint` with the 9 checks from §4.5.
5. Implement `run` as a batch wrapper over `add`.
6. Implement `refresh` and `remove` last.
7. Dogfood on the `agentic-ai-wiki/` test wiki — re-run the full pass end-to-end with the skill instead of by hand. Confirm parity with the manual pass output.
8. Bug-fix pass, then graduate out of "draft 1" status.

Phase 2 (Python CLI) begins only after the skill is stable end-to-end.
