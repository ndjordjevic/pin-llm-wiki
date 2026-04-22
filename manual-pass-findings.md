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

*(fill in after completing Step 2)*

### Fetch

### Ingest

### Findings

---

## Step 3: Web — langchain.com

*(fill in after completing Step 3)*

### Fetch strategy used
<!-- WebFetch → Jina Reader → direct docs URL — record which worked and what the others returned -->

### Ingest

### Findings

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
| 1 | superpowers | | | |
| 2 | youtube | | | |
| 3 | langchain | | | |
| 4 | lint | | | |
| 5 | agent test | | | |

---

## Changes to make in research.md after this pass

*(running list — add entries as they come up)*

