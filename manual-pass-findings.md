# Manual Pass Findings

**Wiki under test:** `/home/ndjordjevic/Projects/LLM/agentic-ai-wiki/`
**Date started:** 2026-04-21
**Pass plan:** `manual-pass-plan.md`
**Sources:** obra/superpowers (GitHub), XXplTbQR9to (YouTube), langchain.com (web)

---

## Format

Each finding is tagged:

- `[CONFIRMED]` — assumption validated, no change needed in research.md
- `[REVISE]` — assumption was wrong or incomplete, update research.md
- `[DECISION]` — judgment call made during the pass (why, what alternatives were rejected)
- `[RISK]` — something that could break at scale or in a real CLI
- `[OPEN]` — question raised but not resolved this pass

---

## Pre-pass: Environment

- yt-dlp v2026.03.17 confirmed installed
- YouTube video `XXplTbQR9to` confirmed has `en-orig` English transcript track (best quality)
- Video: "Paperclip AI Tutorial: How to Build a Zero-Human Company" by Metics Media, 25:48
- No JS runtime for yt-dlp (deno only) — not a blocker for VTT download
- WebFetch capability: untested against JS-heavy sites (LangChain is Next.js/Vercel — biggest unknown)

---

## Step 1: GitHub — obra/superpowers

### Fetch

- **Tool used:** `gh` CLI (`gh repo view`, `gh api repos/.../readme`, `gh api repos/.../contents/...`)
- **Result:** Success — clean, structured access. No JS rendering issues, no rate limits hit.
- **Sources fetched:** README.md (full), docs/ folder listing + docs/testing.md (full), RELEASE-NOTES.md (top 80 lines), folder listings for skills/, commands/, hooks/, agents/
- **Not fetched:** individual SKILL.md files (not needed at standard depth — the README summarises all 14 skills), scripts/, tests/ source (just noted structure)
- **External URLs discovered:** Discord (https://discord.gg/35wsABTejz), announcement blog (https://blog.fsck.com/2025/10/09/superpowers/), Prime Radiant (https://primeradiant.com) — mentioned in wiki, not scraped per plan
- `[CONFIRMED]` gh CLI is the right tool for GitHub repos — clean, no JS issues, structured JSON responses

### Ingest

- **Raw file:** `raw/github/obra-superpowers.md` — README full text + annotated folder structure + docs/testing.md key points + RELEASE-NOTES highlights
- **Wiki pages created:** 1 (`wiki/sources/superpowers.md`)
- **Topic pages created:** 0 — held off; no cross-source material yet to anchor topics to
- **Pages updated:** wiki/index.md, wiki/overview.md, wiki/log.md, raw/github/README.md, inbox.md

### Findings

- `[CONFIRMED]` One wiki source page is the right unit for a GitHub repo at standard detail. The README + docs gave enough for a complete, useful page without needing to read every SKILL.md.
- `[DECISION]` Held topic pages until cross-source material arrives. "Subagent orchestration" and "TDD in agentic systems" are obvious candidates but need a second source to be more than a stub.
- `[DECISION]` Folder structure overview in raw file captures the shape of the repo without cloning. Important folders annotated (skills/, commands/, hooks/, agents/, docs/, tests/); boilerplate ignored (.gitignore, LICENSE, package.json).
- `[CONFIRMED]` Citation discipline was natural — the raw file is the one source, so every claim cites it. No temptation to hallucinate.
- `[RISK]` If a repo has no README or a very thin one, the "one wiki page" approach breaks down. Need a fallback (clone SKILL.md files, read docs/).
- `[OPEN]` How deep should we go into individual SKILL.md files? At standard depth, README summary was enough. At deep, reading each SKILL.md would be warranted.
- **Token cost fetch:** ~15–20k input tokens (README + docs + listings via gh API)
- **Token cost ingest:** ~8–12k input tokens (raw file → wiki page + supporting files)
- **Total estimate:** ~25–35k tokens for this source at standard depth

### Quality pass (post-ingest review)

`[REVISE]` **Inbox state-section mismatch** — agent flipped `[x]` but left the line under `## Pending`. Fix: CLAUDE.md ingest step must say *move* to `## Completed`, not just mark. Generalizable: any two-section checklist where the section is part of the state needs explicit move semantics.

`[REVISE]` **Self-referential `sources:` frontmatter on source pages** — agent wrote `sources: - "[[superpowers]]"` on `wiki/sources/superpowers.md`. `sources:` semantically means "raw source pages this page draws from," which is only meaningful for topic/synthesis pages. Fix: CLAUDE.md must state that source pages MUST NOT include `sources:`. Research.md §6 frontmatter spec is ambiguous — worth tightening there too.

`[REVISE]` **Citation path format** — CLAUDE.md template showed root-relative (`[...](raw/github/...)`) but Obsidian and standard markdown both resolve link targets relative to the file's location, so root-relative breaks. rp6502-kb uses `../raw/...`. Fix: CLAUDE.md now specifies relative-from-file (`../../raw/...` from wiki/sources/ and wiki/topics/).

`[DECISION]` **Citation banner for single-source pages** — repeating the same `([raw/...])` after every paragraph on a page whose claims all come from one raw file is pure noise. Added rule to CLAUDE.md: use a one-line banner at the top (`_All claims below are sourced from X unless otherwise noted._`); add per-paragraph citations only when a second raw file enters the page. Applied to superpowers.md as a retrofit.

`[OPEN]` **raw/github/README.md schema** — currently `File | Repo | Fetched | Stars | Notes`. Could add `Default branch | Latest release` columns now that we fetch those. Not urgent; the raw file itself records them.

---

## Step 2: YouTube — XXplTbQR9to

### Fetch

- **Tool used:** `yt-dlp --dump-json` (metadata/description/chapters) + `yt-dlp --write-auto-sub --sub-format vtt --skip-download --sub-lang en-orig` (transcript)
- **Result:** Success — `en-orig` English caption track downloaded cleanly (257 KB VTT)
- **VTT parsing:** Rolling-caption format (each cue shows 2 lines, last line is live word-by-word). Strategy: take the first clean line (no `<c>` tags) per cue = the finalized/completed line. Deduplicate consecutive identical lines. Result: clean ~28k char transcript grouped by chapter.
- **Description extraction:** `yt-dlp --dump-json` gave full metadata including description text, timestamped chapters, publish date, channel — all in one call.
- **Chapters:** 6 chapters extracted: Intro / What Is Paperclip? / Get Your Server Running / Create Your Company / Give Your Agents Tools / Put Your Company to Work
- `[CONFIRMED]` yt-dlp + en-orig VTT is the right tool — no JS runtime needed, no ffmpeg needed for subtitle-only download
- `[CONFIRMED]` `--dump-json` is the right first call for any YouTube source — gives description, chapters, upload date, channel, duration before touching the VTT

### Ingest

- **Raw file:** `raw/youtube/XXplTbQR9to-paperclip-tutorial.md` — metadata + description + chapter table + cleaned transcript (sections by chapter heading)
- **Wiki page created:** 1 (`wiki/sources/paperclip-tutorial.md`) — "replace watching" format per plan
- **Topic pages created:** 0 — deferred; cross-source patterns emerging (tool access scoping, human-in-the-loop policy) but single source not enough to anchor a topic page yet
- **Pages updated:** wiki/index.md, wiki/overview.md, wiki/log.md, raw/youtube/README.md, inbox.md

### Findings

- `[CONFIRMED]` One wiki page is the right unit for a tutorial YouTube video at standard detail. The 25-minute video distills to ~1 page covering: what it is, deployment platform, company setup, agent model, tools, workflow.
- `[CONFIRMED]` Description + chapters = the best editorial scaffold. The 6 chapters map directly to wiki sections — no guesswork about structure.
- `[DECISION]` Wiki page covers Brave Search API and Resend by name as the two tool examples — user explicitly requested this. Secrets mechanism (sealing, reuse across agents) also noted since it's a design pattern, not just a tutorial step.
- `[DECISION]` Hostinger VPS named explicitly as the deployment server shown in the tutorial. OpenAI Codex vs Claude API distinction also noted — this is a real choice point for readers.
- `[CONFIRMED]` "Replace watching" acceptance bar met: after reading the wiki page, a reader understands what Paperclip is, how to deploy it, how to set up a company, what agents/heartbeats are, how tools work, and how to assign work — without watching 25 minutes of video.
- `[CONFIRMED]` Citation discipline natural — all claims from single raw file, banner citation used (per CLAUDE.md rule).
- `[RISK]` VTT rolling-caption format is non-trivial to parse correctly — the overlap strategy (take first clean line per cue) works but is fragile. A cleaner approach would be `--sub-format srt` if available, or Whisper for videos without subtitle tracks.
- `[OPEN]` Should raw file preserve full transcript or a condensed version? At 28k chars it's manageable for standard; at deep detail we may want the full transcript with timestamps for pinpoint citation.
- **Token cost fetch:** ~1k input tokens (yt-dlp CLI output, no LLM used for fetch)
- **Token cost ingest:** ~35–45k input tokens (full raw file read → wiki page + supporting files)
- **Total estimate:** ~35–45k tokens for this source at standard depth (mostly ingest, transcript-heavy)

---

## Step 3: Web — langchain.com

### Fetch strategy used

- **Tool:** WebFetch — worked on all pages. No JS-skeleton problem. LangChain uses Next.js/Vercel but pages rendered to readable content.
- **Pages fetched (7 total):**
  1. https://www.langchain.com/ — landing page (products, nav, value prop)
  2. https://docs.langchain.com/ — docs index (product sections, getting-started paths)
  3. https://docs.langchain.com/oss/python/langchain/overview — LangChain framework overview
  4. https://docs.langchain.com/oss/python/langgraph/overview — LangGraph overview
  5. https://docs.langchain.com/langsmith — LangSmith overview
  6. https://docs.langchain.com/oss/python/deepagents/overview — DeepAgents overview
  7. https://docs.langchain.com/llms.txt — full concept index for all products
- **Redirect note:** python.langchain.com → docs.langchain.com (308 permanent). Old domain dead; use docs.langchain.com.
- **404 note:** langchain-ai.github.io/langgraph/concepts/ returns 404. LangGraph docs migrated to docs.langchain.com.
- **Not needed:** Jina Reader, Firecrawl, headless browser. WebFetch sufficient.

### Ingest

- **Raw file:** `raw/web/langchain.com.md` — compiled single file (landing + docs + 4 product overviews + llms.txt)
- **Wiki pages created:** 1 (`wiki/sources/langchain.md`)
- **Topic pages created:** 0 — cross-source patterns visible (human-in-the-loop, tool access, skills) but deferred to lint pass
- **Pages updated:** wiki/index.md (count 2→3), wiki/overview.md (3-source synthesis), wiki/log.md, raw/web/README.md, inbox.md

### Findings

`[CONFIRMED]` **WebFetch sufficient for docs sites** — the #1 unknown from research.md §14 turned out to be a non-issue. LangChain Next.js/Vercel renders fine via WebFetch. No fallback needed.

`[CONFIRMED]` **llms.txt pattern** — LangChain publishes a machine-readable concept index at `/llms.txt`. One fetch returns the full structured concept index for all products. Check for this file first on any docs site before deciding how many pages to crawl.

`[DECISION]` **Single raw file for multi-page web source** — compiled all 7 fetched pages into one `raw/web/langchain.com.md`. Matches the GitHub convention (one compiled file per source). At standard depth, one file is cleaner and easier to cite from.

`[DECISION]` **Raw file naming for web sources** — `raw/web/<domain>.md` (e.g., `langchain.com.md`). Consistent and predictable. For sites needing per-page files at deep detail, could use a `raw/web/langchain.com/` directory instead.

`[CONFIRMED]` **One wiki page for a multi-product site** — a single `wiki/sources/langchain.md` covering all 4 products worked well at standard depth. The "when to use which" section anchors the page and prevents it from being just a feature dump.

`[RISK]` **Stale URLs / domain migrations** — python.langchain.com redirects silently; langgraph GitHub Pages 404s. Automated fetches must follow redirects and log final URLs, not original ones. Stale inbox URLs are a real failure mode.

`[OPEN]` **Cross-source topic pages** — clear patterns across all three sources: human-in-the-loop (all), tool access scoping (all), composable skills/capabilities (Superpowers + DeepAgents). Should become topic pages during lint pass (Step 4).

- **Token cost fetch:** ~12–15k input tokens (7 WebFetch calls, each processed by small model)
- **Token cost ingest:** ~8–10k input tokens (raw file → wiki page + supporting files)
- **Total estimate:** ~20–25k tokens at standard depth (cheapest of the three — structured docs are denser and better organized than video transcripts)

---

## Step 4: Lint pass

*(fill in after completing Step 4)*

---

## Step 5: Agent-consumption test

*(fill in after completing Step 5)*

---

## Aggregate findings

*(fill in at end of pass)*

### What worked well

### What needs to change in research.md

### Decisions that should become design rules

### Open questions for PRD

---

## Token cost log

| Step | Source | Tokens in | Tokens out | Notes |
|---|---|---|---|---|
| scaffold | — | — | — | one-time |
| 1 | superpowers | ~20k | ~8k | |
| 2 | youtube | ~1k (CLI only) | ~40k | transcript-heavy ingest |
| 3 | langchain | | | |
| 4 | lint | | | |
| 5 | agent test | | | |

---

## Changes to make in research.md after this pass

*(running list — add entries as they come up)*

