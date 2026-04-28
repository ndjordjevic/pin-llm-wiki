# pin-llm-wiki — Research & Design Brainstorm

**Date:** 2026-04-21 (updated 2026-04-23 after manual end-to-end pass)
**Status:** Brainstorm / design — **manual pass complete**, ready for PRD
**Goal:** Design a generalized, automated, agent-driven LLM Wiki system inspired by Karpathy's pattern — packaged as a reusable tool.
**Manual-pass findings:** `manual-pass-findings.md` — all §14 risks either confirmed or dismissed; key decisions extracted into design rules (see §15 and §18 below).

---

## 1. Vision

Karpathy's LLM Wiki pattern is powerful but manual:

- You clip web pages by hand (Obsidian Web Clipper)
- You drop files into `raw/` yourself
- You invoke the agent manually per source
- Schema (CLAUDE.md/AGENTS.md) is hand-crafted per project

**pin-llm-wiki** automates the pipeline end-to-end:

```
inbox.md (URL list)
    ↓  [fetch]
raw/  (structured source files)
    ↓  [ingest]
wiki/  (LLM-maintained markdown)
    ↓  [lint] (batched, not per-source)
healthy, linked, queryable knowledge base
```

The human's job shrinks to: **drop URLs into inbox → review wiki output**.

### Load-bearing principles

These are non-negotiable — everything else negotiates around them:

1. **Citations first.** Every factual claim in any wiki page must cite the specific raw file it came from. No citation → no claim. The linter enforces this. Wikis are trusted without re-checking; hallucination is the existential risk.
2. **Raw is immutable.** Never edited, never auto-deleted. Source of truth.
3. **Inbox is human-owned.** The agent marks items `[x]` but never adds, never removes.
4. **Git is the versioning layer.** The wiki *is* a git repo. Every ingest can commit. Rollback is always possible.
5. **The wiki is for both humans and agents.** CLAUDE.md must instruct future coding agents to read `wiki/index.md` before answering questions in-repo. Without that, the wiki is inert.

---

## 2. Core Architecture

### Three layers (same as Karpathy)


| Layer      | Owner        | Description                       |
| ---------- | ------------ | --------------------------------- |
| `inbox.md` | Human        | Checklist of URLs to ingest       |
| `raw/`     | Fetch agent  | Fetched/downloaded source content |
| `wiki/`    | Ingest agent | Compiled, linked, queryable pages |


### New additions vs Karpathy


| Feature             | Karpathy                      | pin-llm-wiki                         |
| ------------------- | ----------------------------- | ------------------------------------ |
| Getting raw content | Manual (Obsidian Web Clipper) | Automated fetch (per source type)    |
| Schema setup        | Manual, per-project           | `init` command with interview        |
| Ingestion trigger   | Manual per source             | Batch from inbox, auto-mark complete |
| Detail level        | Implicit                      | Explicit: `brief / standard / deep`  |
| Packaging           | None                          | Skill → CLI → MCP (phased)           |
| Taxonomy            | Fixed per-project             | Interview-driven, domain-appropriate |


---

## 3. Inbox System

### `inbox.md` format

```markdown
# Inbox

## Pending

- [ ] https://www.langchain.com/
- [ ] https://www.llamaindex.ai/
- [ ] https://github.com/safishamsi/graphify/
- [ ] https://github.com/hilash/cabinet
- [ ] https://www.youtube.com/watch?v=FZxEUAfMNRw

## Completed

- [x] https://openai.com/blog/gpt-4  <!-- ingested 2026-04-21 -->
```

### Source type detection (auto, with override)


| Pattern                                | Detected type | Fetch strategy                                    |
| -------------------------------------- | ------------- | ------------------------------------------------- |
| `github.com/<org>/<repo>`              | GitHub repo   | README + structure + key files (+ optional clone) |
| `youtube.com/watch?v=` or `youtu.be/` | YouTube video | Transcript via yt-dlp                             |
| Everything else                        | Web page      | Landing page + docs discovery                     |


Override syntax: `- [ ] https://example.com <!-- depth:3 detail:deep -->`

Tags supported: `depth:N`, `detail:*`, `skip`, `refresh`, `clone` (github). Source type is inferred from the URL.

### Inbox rules

- Inbox is human-owned — agent marks `[x]` but never adds/removes URLs.
- `<!-- skip -->` tag → agent ignores.
- `<!-- refresh -->` tag → agent re-fetches and updates in place.
- Inbox is the source of truth for "done or not" — survives crashes and partial runs.
- **Move semantics (validated in manual pass):** completed items must be *moved* from `## Pending` to `## Completed`, not just flipped to `[x]`. Section membership is part of the state. Any two-section checklist where the section encodes state needs explicit move semantics. The agent's ingest instruction must say "move", not "mark".

---

## 4. Raw Folder — Source Categories

```
raw/
  web/          -- scraped web pages & docs as .md
  github/       -- repo content (summary .md by default, full clone opt-in)
  youtube/      -- transcripts as .md
  assets/       -- downloaded images referenced by wiki pages
  README.md     -- LLM-maintained index of all raw content
```

Additional source categories can be added later via config (e.g. `pdfs/`, `notes/`).

Each subfolder has a `README.md` kept in sync by the agent.

### Fetch behavior per type

**Web page:**

- **First: check for `<domain>/llms.txt`** — many docs sites (LangChain, Anthropic, etc.) publish a machine-readable concept index. One fetch replaces or scopes the crawl. Validated in manual pass — LangChain's llms.txt gave the full concept list for all 4 products in a single call.
- Fetch landing page
- Discover docs (`/docs`, `/documentation`, `/guide`, sitemap.xml)
- Crawl up to depth: `brief`=1 (landing only), `standard`=docs index + ~10 key pages (or llms.txt + ~4 product overviews), `deep`=full crawl within domain
- Save as `raw/web/<domain>.md` (compiled, one file per source) at brief/standard; `raw/web/<domain>/<page-slug>.md` only at deep.
- Follow redirects and log the *final* URL, not the original (old domains silently redirect; e.g. `python.langchain.com` → `docs.langchain.com`).
- Respect `robots.txt`, rate-limit, set UA.
- **WebFetch is sufficient for JS-heavy modern docs sites** (Next.js/Vercel validated in manual pass). Jina Reader / Firecrawl / headless browser kept as fallback only if WebFetch returns a skeleton on a specific site — not the default.

**GitHub repo:**

- Use `gh` CLI (not WebFetch) — validated in manual pass: structured JSON responses, no JS rendering issues, handles auth.
- Always: README (via `gh api repos/<org>/<repo>/readme`), top-level structure (`gh api .../contents/`), default branch (from `defaultBranchRef`, never assume `main`), latest release tag (via `gh release list --limit 1`).
- `standard`: + docs/ folder, examples/, main module READMEs
- `deep`: + key source files identified by agent
- Branch override: `<!-- branch:X -->` in inbox.md targets a specific branch; otherwise use default.
- Default: save as compiled `raw/github/<org>-<repo>.md` (one file per repo, flat — not nested)
- With `<!-- clone -->`: full `git clone` to `raw/github/<org>-<repo>/` (gitignored)

**YouTube:**

- `yt-dlp --dump-json` first → captures description, chapters, title, channel, duration, upload date in one call. Chapters map directly to wiki-page section headings (validated in manual pass).
- Then `yt-dlp --write-auto-sub --sub-format vtt --skip-download --sub-lang en-orig` for the transcript. `en-orig` is the best-quality track where available.
- Parse VTT: rolling-caption format (each cue shows 2 lines, last line is live word-by-word). Strategy: take the first clean line per cue (no `<c>` tags), deduplicate consecutive identical lines. Group by chapter. SRT format is a cleaner alternative when available.
- Fallback: if no transcript, flag in inbox (`<!-- fetch-failed:no-transcript -->`) and skip
- Save as `raw/youtube/<video-id>-<slug>.md`

---

## 5. Detail Levels


| Level      | Raw fetch                           | Wiki pages per source | Page verbosity                        | Rough token cost (ingest) |
| ---------- | ----------------------------------- | --------------------- | ------------------------------------- | ------------------------- |
| `brief`    | Landing / README / transcript only  | 1 page                | ~300–500 words, bullet-heavy          | ~5–20k tokens             |
| `standard` | + docs index + key sections         | 2–5 pages             | ~500–1000 words, headings + prose     | ~30–100k tokens           |
| `deep`     | Full crawl / full repo / full paper | 5–20+ pages           | Comprehensive, all features, examples | ~200k–1M+ tokens          |


Detail level is **locked at wiki init** and stored in `.pin-llm-wiki.yml`. Per-item override via `<!-- detail:X -->`. No global change after init (to avoid inconsistent wiki pages).

### Cost caveat

`deep` on a large docs site (LangChain, AWS, Kubernetes) can run 500k–2M input tokens per source. At current API rates, a single `deep` ingest of 7 sources could easily hit $10–$50. Init interview surfaces this.

---

## 6. Wiki Structure

```
wiki/
  index.md          -- table of contents (LLM-maintained)
  log.md            -- append-only operations log
  overview.md       -- living synthesis
  sources/          -- one page per ingested source
  syntheses/        -- filed query answers worth keeping
```

A single `syntheses/` folder holds cross-source articles worth keeping.

### Page frontmatter

```yaml
---
type: source | synthesis
tags: [tag1, tag2]
related:
  - "[[page]]"
  - "[[other-page]]"
sources:          # synthesis pages only — see rule below
  - "[[source-page]]"
detail_level: brief | standard | deep
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

**Frontmatter rules (validated in manual pass):**

- `sources:` is **only for synthesis pages** — it lists the source pages they draw from. Source pages themselves MUST NOT include `sources:` (they *are* the source; self-reference is meaningless). A source page with `sources: [[self]]` was the most common bug in the first ingest run.
- `related:` is for cross-references between wiki pages (synthesis ↔ synthesis, source ↔ source). Empty list (`related: []`) is valid when no cross-links exist yet. Resolved at lint time, not ingest time.
- Obsidian-compatible wikilinks must be quoted list items (`- "[[page]]"`), not inline bracket arrays.

### Citation rules

**Paths:**
- Wiki-to-raw links use **relative-from-file paths**, not root-relative. From `wiki/sources/<slug>.md` that's `../../raw/...`; from `wiki/syntheses/<slug>.md` use `../raw/...`. Root-relative breaks in Obsidian and standard markdown renderers.

**Banner vs per-sentence:**
- **Single-source pages** (page draws all claims from one raw file): one banner at the top — `_All claims below are sourced from [../../raw/.../file.md](../../raw/.../file.md) unless otherwise noted._` No per-sentence citations. Validated: per-sentence citations on a single-source page are pure noise.
- **Multi-source pages** (synthesis pages, or source pages that incorporate a second raw file): keep the banner for the primary source; add per-paragraph citations only where a *different* raw file supplies the claim.

**Citation layering (validated):**
- Source pages cite *raw files* (via banner or per-paragraph).
- Overview / synthesis pages cite *`[[source page]]` wikilinks* — they synthesize across sources, not from raw directly. Each layer cites the layer below it.

**Enforcement:** the linter rejects any factual claim without a citation chain reaching a raw file.

### Config file

`.pin-llm-wiki.yml` at repo root (human-editable, versioned):

```yaml
version: 1
created: 2026-04-21
domain: "Agentic GenAI learning journey"
detail_level: standard
source_types: [web, github, youtube]
auto_lint: batch  # never | batch | per-ingest
auto_mark_complete: true
```

---

## 7. Agent Architecture

### MVP: one agent, branching on source type

Earlier draft proposed a FetchOrchestrator with 4 specialized sub-agents. Reverting to a simpler starting point:

- **One ingest agent** that branches per source type (matches how rp6502-kb actually works).
- Sub-agents only when the branching becomes painful — e.g., when web crawling needs long-running scrape sessions that would blow context.
- Claude Code's built-in `Agent` tool with `subagent_type=Explore` is enough for most fetching; spawn only when parallelism matters or context pressure demands it.

### Phasing


| Phase   | Packaging                                     | Use                                        |
| ------- | --------------------------------------------- | ------------------------------------------ |
| 1 (MVP) | Skill-only (`~/.claude/skills/pin-llm-wiki/`) | Prove the workflow end-to-end              |
| 2       | Python CLI (`pip install pin-llm-wiki`)       | Automation, CI, cron, sharing              |
| 3       | MCP server                                    | Native tool calls from any MCP-aware agent |
| 4       | Plugin / Obsidian companion                   | Optional polish                            |


**Validate Phase 1 manually before committing to Phase 2.** The risk is over-investing in packaging before the workflow itself is stable.

### Default entrypoint — one command

Power users want `fetch` / `ingest` / `lint` separately. Day-to-day use should be one command:

```
/pin-llm-wiki add <url>
```

→ detects type, fetches, ingests, marks inbox `[x]`, commits.

The split commands stay for batch processing and debugging.

---

## 8. Ingest Behavior

Generalized from rp6502-kb AGENTS.md:

1. Read relevant `raw/` files for the target source.
2. Create/update `wiki/sources/<slug>.md` with summary + citations + frontmatter.
3. Extract key facts → create or update `wiki/sources/`, `wiki/overview.md`, and any deliberate `wiki/syntheses/` pages.
4. Update `wiki/index.md` (add new pages with one-line descriptions).
5. Update `wiki/overview.md` if the synthesis shifts.
6. Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | <source> | <what changed>`.
7. Mark source `[x]` in `inbox.md`.
8. Optional: `git commit` with message `ingest: <source-slug>`.

### Wiki page expectations per source type

*Product/framework (e.g. LangChain):*

- What it does (1 para) — every claim cited
- Key features (bullets with citations)
- Architecture overview
- Main APIs / abstractions
- When to use / when not to
- Ecosystem / integrations
- Links to raw source pages

*GitHub repo:*

- What it does
- Installation
- Key features
- Architecture (if readable from code/docs)
- Example usage (code blocks from README)
- Maintenance status (last commit, stars at ingest time)

*YouTube video (the "replace watching" test):*

- What the video is about (1 para — you should NOT need to watch it after reading)
- Key points / takeaways (bullets with timestamp citations)
- Notable quotes or code shown
- Context (speaker, series, date)

### Merge/update rules (when a synthesis page already exists)

- Add new facts; do not duplicate.
- If new source contradicts existing claim → add `> **Conflict:*`* block citing both sources; do not silently overwrite.
- Source authority tie-breaker lives in the generated CLAUDE.md (e.g., official docs > repo > blog > YouTube).

---

## 9. Lint — Batched, Not Per-Ingest

Lint looks for *inter-source* connections, which don't exist after ingesting one source. So:

- **Default trigger:** end of an inbox batch processing run.
- **Optional:** manual `/pin-llm-wiki lint` at any time.
- **Not default:** per-ingest lint. Waste.

Lint checks:

1. **Citation coverage** — every factual sentence in every page has a citation chain to a raw file. Load-bearing.
2. **Contradictions** — pages with conflicting claims. Rank by source authority.
3. **Orphans** — pages with no inbound `[[wikilinks]]`. **Includes structural pages** (`overview.md`, `log.md`) — manual pass confirmed these get missed if not in the `index.md` scaffold; the generated `index.md` must link to them.
4. **Data gaps** — cross-source concepts mentioned in `overview.md` but not yet promoted to a synthesis page.
5. **Missing cross-references** — pages that mention other wiki-known entities without linking. Manual pass found 2 of 3 source pages had empty `related:` — resolving cross-refs is a lint-time responsibility, not ingest-time.
6. **Stale sources** — sources last refreshed > **30 days** ago (configurable default). Fast-moving projects may need a shorter threshold; evergreen docs a longer one.
7. **Terminology collisions** — same term used for different concepts across sources (manual pass found "skills" in Superpowers vs DeepAgents). Flag for disambiguation via a synthesis page or a note on both source pages.

Lint reports findings; it doesn't auto-fix. Fixes are a separate user-driven pass — with two exceptions considered for auto-fix:
- Add `overview.md` / `log.md` links to `index.md` if missing (structural, no judgment needed).
- Report candidate synthesis pages when a repeated cross-source concept deserves its own page.

### Synthesis-page creation timing (validated)

Synthesis pages are **manual**, not ingest-time artifacts. Ingest creates source pages only. Cross-source syntheses require enough evidence and editorial judgment to justify their own page.

### Agent-consumption harvest (new workflow)

When a fresh agent session produces a synthesis insight better than what's in the wiki — e.g., a comparison table that the overview lacks — that insight is a candidate to write back into a synthesis page. The manual pass Step 5 demonstrated this: the agent's answer to a cross-source question was more precise than `overview.md`'s treatment of the same subject. Harvest is a manual step for MVP; formalize as a command (`/pin-llm-wiki harvest`) in a later phase.

---

## 10. Init Flow & Interview

`/pin-llm-wiki init` in an empty folder → conversational interview:

1. **What is this wiki about?** (free text, domain description)
2. **Detail level?** `brief / standard / deep` — shows estimated cost per typical source
3. **Which source types will you use?** (multi-select: web, github, youtube — more can be added later)
4. **Git:** initialize repo now? (default: yes)
5. **Lint cadence:** `batch` (end of run) / `per-ingest` / `manual only`
6. **Auto-mark inbox `[x]` after ingest?** (default: yes)
7. **Privacy:** any domains to allowlist or blocklist for scraping?

Answers → written to `.pin-llm-wiki.yml` and baked into generated `CLAUDE.md` / `AGENTS.md`.

### Generated scaffold

```
<wiki-folder>/
  .git/                          (if git enabled)
  .pin-llm-wiki.yml
  .gitignore                     (excludes raw/github/<clones>/, assets cache, etc.)
  inbox.md
  CLAUDE.md                      (instructs agents to read wiki/index.md first)
  AGENTS.md
  raw/
    web/README.md
    github/README.md
    youtube/README.md
    assets/
  wiki/
    index.md          (links to overview.md and log.md by default)
    log.md
    overview.md
    sources/
    syntheses/
```

**Index scaffold:** generated `index.md` must include navigation links to `overview.md` and `log.md` out of the gate. Manual pass confirmed these get missed otherwise.

### Generated CLAUDE.md — load-bearing instructions

Every generated CLAUDE.md must include:

```markdown
## For AI agents working in this repo

Before answering any question about this wiki's domain, you MUST:
1. Read `wiki/index.md` to identify relevant pages.
2. Follow `[[wikilinks]]` to drill in.
3. Cite wiki page names in your answer.
4. If the answer is not in the wiki, say so, then fetch current information online instead of relying on training data alone.
```

Without this, the wiki is just files on disk. With it, the wiki becomes the coding agent's context.

---

## 11. Full Flow Example — "Agentic GenAI Learning Journey"

1. `mkdir agentic-ai-wiki && cd agentic-ai-wiki`
2. `/pin-llm-wiki init` → interview → scaffold + git init
3. Populate `inbox.md`:

```markdown
- [ ] https://www.langchain.com/
- [ ] https://www.llamaindex.ai/
- [ ] https://github.com/safishamsi/graphify/
- [ ] https://github.com/hilash/cabinet
- [ ] https://github.com/obra/superpowers
- [ ] https://github.com/gsd-build/get-shit-done
- [ ] https://www.youtube.com/watch?v=FZxEUAfMNRw&list=PLmk_-gnv1YVL8Lk170JCrYZ4h_tWBrkYm
```

1. `/pin-llm-wiki run` — processes all pending inbox items:
  - Detects types, fetches each, saves to `raw/`
  - Ingests each into `wiki/`
  - Marks inbox `[x]`
  - Runs a single lint pass at the end
  - Commits (if enabled)
2. Review in Obsidian or preferred markdown viewer.
3. Ask the coding agent a question — it reads `wiki/index.md`, drills into source pages and syntheses, cites pages.

**Time budget:** ~2 minutes of human time (write inbox, kick off run, review). LLM time: minutes to hours depending on detail level and source count. LLM cost: $1–$50 depending on detail level (init interview surfaces this up front).

---

## 12. Wiki Update Strategy

### Adding sources

- Drop URL in `inbox.md` → `/pin-llm-wiki add` or `/pin-llm-wiki run`.
- Agent merges into existing synthesis pages when they exist; doesn't duplicate.

### Refreshing sources

- Tag: `- [ ] https://... <!-- refresh -->`
- Fetch agent re-fetches, computes hash of cleaned content.
- If hash differs: update raw file, ingest agent updates touched wiki pages, log the refresh.
- If hash identical: skip, log as "no change."

### Removing sources

- `/pin-llm-wiki remove <slug>` → deletes `raw/<type>/<slug>` and `wiki/sources/<slug>.md`.
- Lint runs automatically after a remove: flags orphaned `[[wikilinks]]` and sentences that cited the removed source.
- User decides: rewrite those sentences (re-cite from another source) or drop them.
- **Soft-delete first?** Move to `wiki/.archive/` before hard-delete — configurable.

### Schema migrations (CLAUDE.md / AGENTS.md changes)

- `version` bumps in `.pin-llm-wiki.yml`.
- Migration script reformats existing pages if needed.
- Rare.

---

## 13. Scaling — Search & Wiki Memory

Karpathy runs at ~100 articles / ~400k words and notes `index.md` alone starts to creak. Plan for this.

- **Phase 1 (skills-only, small wikis):** `index.md` is enough. Agent reads it first each session.
- **Phase 2 (CLI):** integrate [qmd](https://github.com/tobi/qmd) or similar — local hybrid BM25+vector search over the wiki.
- **Wiki memory for agents:** on each query, the agent should load `wiki/index.md` + `wiki/overview.md` + targeted pages. Avoid re-reading everything. Overview doubles as a compressed summary of the whole wiki.

---

## 14. Risks & Unknowns

Things I handwaved over. Must be validated in manual pass.

### Fetching is harder than it looks

- ~~**JS-heavy docs sites** (Vercel, Mintlify, Next.js, Docusaurus): `WebFetch` often returns skeletons.~~ **Dismissed after manual pass.** WebFetch handled LangChain (Next.js/Vercel) without skeleton problems. Keep Jina Reader / headless browser as fallback for specific failures, not default.
- **Rate limits & bot detection** on Cloudflare-fronted sites — still a real risk, not exercised by manual pass.
- **SPAs with client-side routing** — crawling by href often misses real content URLs. Mitigated by the llms.txt discovery pattern (fetch llms.txt first; only crawl if absent).
- **robots.txt & ToS** — some sites forbid scraping; need allowlist and respectful defaults.
- **Stale URLs / domain migrations** (new from manual pass): `python.langchain.com` silently redirects to `docs.langchain.com`; deprecated doc sites 404. Fetch layer must follow redirects and log the *final* URL.

### Transcripts

- YouTube auto-subs are often poor quality (hallucinated punctuation, wrong speakers).
- Many videos have transcripts disabled.
- Need graceful failure: flag the inbox item, skip, continue the batch.

### GitHub repos

- Size variance: 100-file toy repo vs 10k-file enterprise codebase. "Read key files" is vague.
- Monorepos complicate "what's the project about?"
- Rate limits on unauthenticated GitHub API calls.

### Cost and time

- `deep` ingest on a large source is expensive and slow. Need progress indicators, cost estimates before starting, dry-run mode.
- No way to cap total spend yet — should have a budget guard.

### Hallucination (the real existential risk)

- Citations must be enforced by lint. A wiki page without citations is worse than no wiki — it's confident-sounding misinformation that the human will trust and that the next agent will use as context.
- Need: lint can flag un-cited claims; ingest prompt explicitly requires per-sentence citations for key claims.

### Idempotency

- What if `pin run` crashes at source 4 of 7?
  - Sources 1–3 marked `[x]`, source 4 partially in `raw/`, wiki half-updated.
  - Recovery: `pin run` re-reads inbox, finds unchecked items, re-fetches only those. Partial raw files should be detectable (size/hash check) and discarded.
- Every operation should be resumable by re-running.

### Privacy / security

- Scraping respects `robots.txt` and user-supplied allowlists.
- No API keys in `raw/` or `wiki/`.
- Some users point this at internal docs behind auth — auth story is out of scope for MVP.

### Wiki integrity under deletion

- Removing a source can orphan `[[wikilinks]]` across 15+ pages. Lint must catch this. Soft-delete by default.

### Multi-user / team

- Out of scope for MVP (Karpathy's pattern is single-user).
- Git provides merge capability but conflict resolution in LLM-generated markdown is nontrivial.

---

## 15. Open Questions & Decisions


| #   | Question                      | Options                                          | Lean                                                                     |
| --- | ----------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------ |
| 1   | CLI vs skills-first?          | CLI from start vs skills → CLI                   | Skills first, CLI phase 2 ✓                                              |
| 2   | GitHub raw: clone or summary? | Full clone vs .md summary                        | Summary default, `--clone` opt-in (open)                                 |
| 3   | Detail level changeable?      | Lock at init vs per-item override only           | Lock global, per-item override ✓                                         |
| 4   | Web scraping engine           | WebFetch vs headless browser vs Jina/Firecrawl   | WebFetch first, fall back to Jina Reader if skeletons (needs validation) |
| 5   | Transcript tool               | yt-dlp vs YouTube API                            | yt-dlp                                                                   |
| 6   | Auto-lint timing              | Never / per-ingest / batched                     | **Batched** (changed from earlier draft)                                 |
| 7   | Refresh diff                  | Hash vs date vs LLM                              | Hash ✓                                                                   |
| 8   | Multi-LLM support             | Claude-only vs agnostic                          | Claude-first, abstract later                                             |
| 9   | Init interview UX             | Conversational vs form                           | Conversational                                                           |
| 10  | Detail level naming           | low/mid/high vs brief/standard/deep              | **brief/standard/deep** ✓                                                |
| 11  | Default command               | Split (fetch/ingest/lint) vs combined (`add`)    | Combined `add` is default, split for power users                         |
| 12  | Agent architecture            | Sub-agents per type vs one agent branching       | One agent branching (MVP); sub-agents if needed later                    |
| 13  | Git integration               | Optional vs required                             | Required by default, can opt out                                         |


---

## 16. Next Steps

1. **Manual end-to-end pass** on 3 diverse URLs (1 web/docs, 1 github, 1 youtube) in Claude Code. Goal: surface which risks in §14 are real vs paranoia.
2. **Update this doc** with findings from the manual pass.
3. **Draft PRD.md** reflecting what was learned — scope, user stories, MVP spec, acceptance criteria.
4. Design generic `CLAUDE.md` / `AGENTS.md` template.
5. Build init skill (scaffolding + interview).
6. Build fetch+ingest skills — one source type at a time (start with GitHub: lowest-risk fetching).
7. Test full flow on the 7-URL agentic AI inbox.
8. Evaluate CLI packaging once skills are stable.

---

## 17. Name

`pin-llm-wiki` — connects to the `pinrag` family of projects. "pin" = bookmark/pin knowledge. Decided.

---

## 18. Manual-pass validation summary (2026-04-23)

Three sources ingested by hand into `agentic-ai-wiki/`: obra/superpowers (GitHub), a YouTube tutorial (XXplTbQR9to), and langchain.com (web docs). Detail level: standard. Full notes in `manual-pass-findings.md`. Results relevant to this doc:

### Confirmed principles (don't second-guess in PRD)

- **Citations-first works.** Banner + per-paragraph model produced zero hallucinations across 3 sources and 1 agent-consumption test.
- **Wiki-for-agents works.** A fresh Claude Code session, given only `CLAUDE.md` + `wiki/`, produced a cited, synthesized, cross-source answer with no training-data contamination. Principle #5 (wiki is for both humans and agents) validated at 3-source scale.
- **One compiled raw file per source** is the right granularity at brief/standard. Per-page files only at deep.
- **Keep synthesis pages manual.** Ingest creates source pages only. Cross-source synthesis pages should be created only when they add durable value.

### Dismissed risks (move out of §14 concern list)

- WebFetch on JS-heavy docs sites. LangChain rendered fine.

### New rules adopted into the design (integrated above)

- llms.txt discovery pattern (§4).
- Inbox move semantics (§3).
- Relative-from-file citation paths (§6).
- Banner vs per-paragraph citation (§6).
- Topic pages at lint time, cross-refs resolved at lint time (§9).
- Orphan lint for structural pages (§9).
- Staleness threshold: 30d default (§9).
- Agent-consumption harvest workflow (§9).
- Redirect-follow with final-URL logging (§4, §14).
- Citation layering: synthesis → `[[source]]` → raw (§6).

### Still open for PRD to decide

- Should lint stay purely report-only, or ever auto-propose synthesis candidates in a structured way?
- Citation semantics for synthesis/overview pages — confirmed `[[source pages]]` is right, but `overview.md` currently has no citations at all. Should this be enforced?
- Deep-detail raw layout — flat compiled file vs per-page directory.
- Formal harvest command (`/pin-llm-wiki harvest`) — MVP or Phase 2?

### Token cost reality check

Full 3-source pass at standard depth: ~98k combined input/output tokens. Well under the 200k guard rail. At current API rates: roughly $0.50–$1.50 per full pass. Init interview cost estimates can be confident for brief/standard; deep still open.

---
