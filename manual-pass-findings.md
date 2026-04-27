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

**Scope:** 3 source pages (`superpowers.md`, `paperclip-tutorial.md`, `langchain.md`), 2 operational pages (`index.md`, `log.md`), 1 synthesis page (`overview.md`). Topics/ and syntheses/ directories are empty.

Checks follow `research.md §9` order.

---

### Check 1: Citation coverage

- `[CONFIRMED]` **superpowers.md** — banner citation in place (`_All claims below are sourced from ../../raw/github/obra-superpowers.md..._`). Single-source page; no per-sentence citations needed per CLAUDE.md rule. ✅
- `[CONFIRMED]` **paperclip-tutorial.md** — banner citation in place. Single-source page. ✅
- `[CONFIRMED]` **langchain.md** — banner citation in place. Single-source page. ✅
- `[OPEN]` **overview.md** — synthesized document; no citations of any kind. Draws on wiki source pages, not raw files directly. Structural ambiguity: should synthesis/overview pages cite `[[source pages]]` or raw files? Currently cites neither. The citations are one hop removed (overview → source page → raw file). PRD needs to define citation semantics for synthesis-layer documents.
- `[CONFIRMED]` `index.md` and `log.md` are operational files with no factual claims requiring citation. ✅

**Summary:** All source pages are citation-clean. One structural open question on synthesis docs.

---

### Check 2: Contradictions

- No factual contradictions found across the 3 source pages.
- `[OPEN]` **"Skills" terminology collision** — "skills" means materially different things in Superpowers (markdown instruction files injected at session-start into a coding agent) vs DeepAgents (reusable capability code modules). Not a factual contradiction — two different things sharing a name — but a reading hazard. The `langchain.md` DeepAgents section already notes "compare: Superpowers skills" in plain text. This needs disambiguation, ideally via a topic page or a note on both source pages. Noted in `overview.md` as an open question.
- `[CONFIRMED]` No contradictions on human-in-the-loop, tool access scoping, or agent orchestration claims across sources.

---

### Check 3: Orphans (pages with no inbound wikilinks)

- `[ISSUE]` **`wiki/overview.md`** — no inbound `[[wikilinks]]` from any wiki page, including `index.md`. `index.md` has a Sources section, Topics section, and Syntheses section, but no link to `overview.md`. Orphan.
- `[ISSUE]` **`wiki/log.md`** — no inbound `[[wikilinks]]` from any wiki page. `index.md` does not link to it. Orphan.
- `[CONFIRMED]` `wiki/sources/superpowers.md` — linked from `index.md` (`[[superpowers]]`) and from `paperclip-tutorial.md` related frontmatter. ✅
- `[CONFIRMED]` `wiki/sources/paperclip-tutorial.md` — linked from `index.md` (`[[paperclip-tutorial]]`). ✅
- `[CONFIRMED]` `wiki/sources/langchain.md` — linked from `index.md` (`[[langchain]]`). ✅

**Fix needed:** `index.md` should have navigation links to `overview.md` and `log.md`. CLAUDE.md ingest prompt should include these as standard links in the index scaffold.

---

### Check 4: Data gaps (concepts mentioned but no topic page)

Three cross-source patterns are explicitly named in `overview.md` but have no topic pages:

| Concept | Sources | Status |
|---|---|---|
| **Tool access scoping** | All 3 | Strongest candidate — explicitly named in overview, mechanism differs per source |
| **Human-in-the-loop by policy** | All 3 | Strongest candidate — interrupt mechanisms differ (Superpowers: review checkpoints; Paperclip: board inbox; LangGraph: graph interrupts) |
| **Layered/composable agent architecture** | All 3 | Named pattern — each source has a different layering model |

Additional candidates from findings and source content:

| Concept | Sources | Notes |
|---|---|---|
| **Subagent orchestration** | Superpowers + LangGraph/DeepAgents | Named in Step 1 findings as deferred candidate |
| **Skills as capability unit** | Superpowers + DeepAgents | Disambiguation needed (see Check 2) |
| **Agent observability / evaluation** | LangSmith (1 source) | Single-source so far; topic page premature but gap noted |
| **Persistent vs session-based agents** | Paperclip heartbeat vs Superpowers session | Pattern difference not yet named as a topic |
| **TDD in agentic systems** | Superpowers (1 source) | Single-source; premature for topic but gap noted |

`[DECISION]` Topic pages were intentionally deferred during Steps 1–3 (insufficient cross-source material per Step 1 findings decision). Lint now confirms 3 topics are ready to be created: tool access scoping, human-in-the-loop, and layered architecture — each has 3-source coverage. Remaining candidates need a second source.

---

### Check 5: Missing cross-references

- `[ISSUE]` **`langchain.md` body text** — DeepAgents "Skills" row says `"Reusable capability modules (compare: Superpowers skills)"` in plain text. No `[[superpowers]]` wikilink. Reader navigating `langchain.md` gets no link to jump to the comparison.
- `[ISSUE]` **`langchain.md` frontmatter** — `related: []` is empty. Should include `[[superpowers]]` (skills comparison is explicit in body) and `[[paperclip-tutorial]]` (heartbeat vs LangGraph durable execution contrast is an open question in `overview.md`).
- `[ISSUE]` **`superpowers.md` frontmatter** — `related: []` is empty. Should include `[[langchain]]` given the explicit skills/DeepAgents comparison and shared human-in-the-loop pattern.
- `[CONFIRMED]` **`paperclip-tutorial.md`** — `related: ["[[superpowers]]"]` is set. ✅ Only source page with a cross-reference.
- `[CONFIRMED]` Overview.md names all three sources but is a synthesis doc — no wikilinks required by current convention.

**Summary:** 2 of 3 source pages have empty `related:` frontmatter despite documented cross-source connections. 1 inline wikilink missing.

---

### Check 6: Stale sources

- `superpowers.md`: fetched 2026-04-22, ingested 2026-04-22 (1 day old) ✅
- `paperclip-tutorial.md`: fetched 2026-04-23, ingested 2026-04-23 (today) ✅
- `langchain.md`: fetched 2026-04-23, ingested 2026-04-23 (today) ✅

`[OPEN]` No stale sources at this time. However, the staleness threshold ("N days" in `research.md §9`) is undefined. For fast-moving projects like Superpowers (v5.0.7, active development) and LangChain (ongoing OSS), a 30-day threshold seems reasonable. PRD needs to define this.

---

### Lint pass summary

| Check | Status | Issues |
|---|---|---|
| Citation coverage | ✅ Clean | 1 open question on synthesis docs |
| Contradictions | ✅ Clean | 1 terminology collision to disambiguate |
| Orphans | ⚠️ 2 issues | `overview.md` and `log.md` not linked from `index.md` |
| Data gaps | ⚠️ 3 ready, 6 noted | 3 topic pages ready to create; 6 more candidates |
| Missing cross-refs | ⚠️ 3 issues | `related:` empty on 2 source pages; 1 inline link missing |
| Stale sources | ✅ Clean | Freshness threshold undefined for PRD |

`[DECISION]` Per plan: findings recorded, no fixes applied. Next step is Step 5 (agent-consumption test) or a fix pass depending on user preference.

---

## Step 5: Agent-consumption test

**Question asked:** "What's the difference between how superpowers and LangChain approach agent tool use?"
**Session:** Fresh Claude Code session opened in `agentic-ai-wiki/`.

### Observations

**Did the agent follow CLAUDE.md and read `wiki/index.md` first?**
`[CONFIRMED]` Yes — first action was "Let me read the wiki index first to find the relevant pages." Read 3 files (index + 2 source pages) before generating any output. CLAUDE.md load-bearing instruction worked.

**Did it cite wiki page names?**
`[CONFIRMED]` Yes — cited `[[superpowers]]` and `[[langchain]]` as wikilinks in the response body. Not buried in a footnote — inline, as the wiki pages are identified.

**Was the answer synthesized from the wiki, or hallucinated from training data?**
`[CONFIRMED]` Synthesized from wiki. The answer reflects exact wiki content:
- "Tools are instruction sets (.md files), not code functions" — directly from `superpowers.md` skill definition section
- "Session-start hook injects a bootstrap" — verbatim concept from `superpowers.md`
- LangChain's three-layer tool model (LangChain / LangGraph / DeepAgents) — correct and precise per `langchain.md`
- "DeepAgents is the closest LangChain product to Superpowers" — cross-source synthesis that exists in `overview.md` as an open question; the agent resolved it rather than just restating it

No hallucinated facts detected. Every claim maps back to wiki content.

### Quality of output

The agent went beyond just restating facts — it produced a novel comparison table with 5 dimensions not pre-computed anywhere in the wiki. The synthesis ("Superpowers encodes tool use as methodology; LangChain encodes it as mechanism") is an emergent insight that doesn't appear verbatim in any wiki page but is directly entailed by the wiki's content.

This is better than expected: not just retrieval, but valid reasoning over the wiki graph.

### Issues surfaced

`[CONFIRMED]` **Orphan issue from lint pass confirmed real** — the agent read `wiki/index.md` and jumped directly to source pages. It did not read `overview.md` (which contains the most synthesized cross-source thinking). This is because `overview.md` is not linked from `index.md` (confirmed orphan from Check 3). The agent missed the pre-computed synthesis layer.

`[OPEN]` **Agent produced a better answer than the wiki's own overview** — the comparison table is more precise than what `overview.md` says about tool use. This raises a question: should the lint/fix pass after an agent-consumption test be used to harvest agent-generated insights back into topic pages? That's an emergent workflow not anticipated in the plan.

### Verdict

**Core principle validated**: the wiki works for agents. A fresh session with no training-data context — just CLAUDE.md + wiki/ — produced a synthesized, cited, wiki-grounded answer to a non-trivial cross-source question.

`[CONFIRMED]` "Wiki for both humans and agents" principle holds at this scale (3 sources, standard depth).

---

## Aggregate findings

### What worked well

1. **Fetch layer — all three types worked on first attempt.** gh CLI for GitHub (clean structured JSON), yt-dlp for YouTube (VTT + metadata in two calls), WebFetch for docs sites (no JS-skeleton issue). No fallback tools needed for any source.
2. **Citation discipline — banner pattern is the right solution for single-source pages.** Per-sentence citations on pages that draw from one raw file are pure noise. A one-line banner + per-paragraph citations when a second raw file enters the page strikes the right balance. Easy to write, easy to verify.
3. **"One compiled file per source" convention.** Compiling all fetched content for a source into a single raw file (e.g. `langchain.com.md` from 7 pages) keeps the citation target unambiguous. Source pages don't need to track which sub-page a claim came from — the raw file is the citation unit.
4. **Wiki-for-agents principle validated end-to-end.** A fresh Claude Code session, given only CLAUDE.md + wiki/, produced a synthesized, cited, wiki-grounded answer to a non-trivial cross-source question. No hallucinations detected. The agent followed CLAUDE.md, read the index first, and cited `[[wikilinks]]` inline.
5. **Structured methodology over ad-hoc ingest.** Deferring topic pages until cross-source material arrived (Steps 1–3) and then creating them in the lint pass (Step 4) produced a clean wiki at end-of-pass rather than premature stubs.
6. **llms.txt pattern discovered.** Docs sites that publish `/llms.txt` give a one-fetch structured concept index for the entire site. Check for it before deciding how many pages to crawl.

---

### What needs to change in research.md

1. **§14 risk "WebFetch fails on JS-heavy docs sites" → dismiss.** LangChain (Next.js/Vercel) rendered fine. Risk was real to anticipate but didn't materialize. Move to "Risks that turned out to be paranoia."
2. **§6 frontmatter spec: tighten `sources:` field semantics.** `sources:` should only appear on topic/synthesis pages (listing the raw sources they draw from). Source pages must NOT include `sources:` — they ARE the source. Currently ambiguous.
3. **§6 or §7: add citation path convention.** Links from wiki pages to raw files must be relative-from-file (e.g. `../../raw/github/...` from `wiki/sources/`), not root-relative. Root-relative breaks in Obsidian and standard markdown renderers.
4. **§7 or new section: add citation banner rule.** Single-source pages: use one banner line at top, no per-sentence citations. Multi-source pages: per-paragraph citations when a new raw file enters.
5. **New section or §11: add llms.txt pattern.** Before crawling a docs site, check `<domain>/llms.txt`. If it exists, fetch it first — it may replace crawling entirely or dramatically reduce page count needed.
6. **§5 inbox semantics: "move, don't just mark."** The ingest step must *move* completed URLs from `## Pending` to `## Completed`, not just flip `[x]`. Any two-section checklist where section membership is part of the state needs explicit move semantics. Update CLAUDE.md ingest step.
7. **§9 lint checks: add staleness threshold as a PRD decision.** The check exists but N is undefined. For fast-moving projects, 30 days seems right; research.md should name the default and flag it as configurable.

---

### Decisions that should become design rules

1. **Topic pages are created at lint time, not ingest time.** Ingest creates source pages only. Topic pages require cross-source evidence. Lint identifies when enough evidence exists. This prevents premature stubs and keeps the ingest step focused.
2. **Deferred cross-references are resolved at lint time.** `related:` frontmatter and inline wikilinks to other sources should be set at lint time, once all sources for a batch are ingested. Setting them at ingest time requires forward-knowledge the agent doesn't have.
3. **Raw directory convention: one compiled file per source.** GitHub: `raw/github/<org>-<repo>.md`. YouTube: `raw/youtube/<video-id>-<slug>.md`. Web: `raw/web/<domain>.md` (or `raw/web/<domain>/` for deep detail multi-page sites).
4. **`index.md` must link to `overview.md` and `log.md` in its scaffold.** These are structural pages, not source pages, but they are part of the navigation graph. Orphan lint confirmed they get missed if not in the index scaffold from the start.
5. **Source pages must cite a raw file; overview/synthesis docs cite `[[source pages]]`.** Citation chain: synthesis → `[[source page]]` → `raw/...`. Each layer cites the layer below it. overview.md citing source pages (as wikilinks) is sufficient for that layer.
6. **Agent-consumption outputs are candidates for harvest back into topic pages.** When a fresh agent session produces a synthesis insight better than what's in the wiki, that insight should be written into the relevant topic page. This closes the loop: wiki improves over use.

---

### Open questions for PRD

1. **Staleness threshold** — what is the default N for "stale source" lint check? 30 days? Configurable per source type? Fast-moving (GitHub active dev) vs slow-moving (evergreen docs) may need different thresholds.
2. **Citation semantics for synthesis-layer docs** — should `overview.md` / synthesis pages cite `[[source page wikilinks]]`, raw file paths, or both? Current convention (none) was an oversight. Recommend: cite `[[source pages]]` at synthesis layer.
3. ~~**Topic page creation trigger** — should lint *suggest* topic pages (report only) or *create stubs* (auto-fix)?~~ **Resolved:** report-only by default (`topic_creation: report`). Auto-stub creation is kept as a legacy opt-in. Threshold raised to ≥3 distinct products, counted by `product:` frontmatter — empty stubs from same-product source pairs (marketing site + own GitHub repo) were the failure mode that prompted this resolution.
4. **Deep detail raw file structure** — for web sources at `deep` detail, should we use a flat compiled file (`langchain.com.md`) or a directory with per-page files (`langchain.com/intro.md`, `langchain.com/langgraph.md`)? Flat is simpler; directory is more navigable and supports per-page citation.
5. **VTT parsing robustness** — yt-dlp's rolling-caption VTT format is non-trivial to parse. Should the CLI include a built-in VTT → markdown converter, or document the parsing strategy for CLAUDE.md? SRT format alternative if available?
6. **Harvesting agent outputs** — is there a formal "harvest" workflow where insights generated during agent-consumption tests are written back into the wiki? Or is this a manual step left to the user?
7. **Lint auto-fix scope** — which lint findings should be auto-fixable vs report-only? Candidates for auto-fix: add `overview.md`/`log.md` links to index, add `related:` cross-refs, create topic stubs. Candidates for report-only: contradictions, citation gaps (require human judgment).

---

## Token cost log

| Step | Source | Tokens in | Tokens out | Notes |
|---|---|---|---|---|
| scaffold | — | — | — | one-time |
| 1 | superpowers | ~20k | ~8k | |
| 2 | youtube | ~1k (CLI only) | ~40k | transcript-heavy ingest |
| 3 | langchain | ~13k | ~9k | 7 WebFetch calls + ingest; cheapest source |
| 4 | lint | 0 | 0 | manual pass — no LLM calls |
| 5 | agent test | ~5k | ~2k | index + 2 source pages read; small output |
| **Total** | | **~39k** | **~59k** | ~98k combined; well under 200k guard rail |

---

## Changes to make in research.md after this pass

1. **§14 → dismiss "WebFetch fails on JS-heavy sites"** — WebFetch worked on LangChain (Next.js/Vercel). Paranoia, not a real risk.
2. **§6 frontmatter spec → tighten `sources:` field** — source pages must NOT include `sources:`; that field is only for topic/synthesis pages.
3. **§6 or §7 → add relative citation path rule** — links from wiki pages to raw files must be relative-from-file, not root-relative.
4. **§7 or new → add citation banner rule** — single-source pages use a banner, not per-sentence citations; multi-source pages add per-paragraph citations when a new raw file enters.
5. **New → add llms.txt discovery pattern** — check `<domain>/llms.txt` before crawling any docs site.
6. **§5 inbox → add move semantics rule** — ingest must move completed URLs from Pending to Completed, not just mark `[x]`.
7. **§9 → define staleness threshold N** — add configurable default (suggest 30 days) to lint check specification.
8. **§9 or new → add orphan lint for structural pages** — `overview.md` and `log.md` must be linked from `index.md`; lint should check structural pages, not just user-created pages.
9. **New → add "agent-consumption harvest" workflow** — insights generated during agent-consumption tests are candidates to write back into topic pages.

