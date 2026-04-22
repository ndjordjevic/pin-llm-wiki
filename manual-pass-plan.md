# Manual End-to-End Pass — Plan

**Date:** 2026-04-21
**Status:** Ready to execute
**Goal:** Run the pin-llm-wiki flow by hand on 3 diverse sources. Surface which risks in `research.md §14` are real vs paranoia. Inform the PRD.

---

## Success criteria

By the end of this pass, we should be able to answer:

1. **Fetching per type** — does `WebFetch` work for a docs site, or do we need Jina Reader / Firecrawl / headless browser?
2. **Citation discipline** — can the ingest agent actually cite every claim back to a specific raw file? How does it fail?
3. **Topics structure** — does the single `topics/` folder stay coherent across three diverse sources, or do pages blur into each other?
4. **Wiki pages per source** — what does `standard` detail actually produce? Is the per-type template (landing page replacer for web, README-based for github, "replace watching" for youtube) the right shape?
5. **Token cost** — what does a real `standard` ingest cost in tokens / dollars for each source type?
6. **Idempotency** — if we crash partway, can we resume cleanly?
7. **Merge behavior** — when source 2 adds to a topic created by source 1, does it extend cleanly or duplicate?
8. **CLAUDE.md-as-agent-instruction** — after ingest, if we ask a fresh Claude Code session a question, does it actually follow the CLAUDE.md and read `wiki/index.md` first?

---

## Sources

Three deliberately diverse sources — one per core type we care about for MVP:

| # | Type | URL | Why this one |
|---|---|---|---|
| 1 | Product / docs site | https://www.langchain.com/ | Large JS-heavy site with deep docs — tests the hardest web case |
| 2 | GitHub repo | https://github.com/obra/superpowers | Mid-sized, substantive README, agent-focused — relevant to the wiki theme |
| 3 | YouTube video | https://www.youtube.com/watch?v=XXplTbQR9to (playlist `PLmk_-gnv1YVL8Lk170JCrYZ4h_tWBrkYm`) | Real inbox candidate; tests transcript fetch |

**Detail level:** `standard` for all three. Reason: `brief` may be too shallow to stress-test merging across sources; `deep` will burn tokens before we even know the design works.

**Theme for the wiki:** "Agentic GenAI Learning Journey" (matches the full-flow example in `research.md §11`).

---

## Pre-flight

1. Create the test workspace:
   ```
   /home/ndjordjevic/Projects/LLM/agentic-ai-wiki/
   ```
2. `git init` inside it. Commit nothing yet.
3. Hand-write the initial scaffold (no `init` skill yet — that's what we're validating):
   ```
   .pin-llm-wiki.yml         # hand-written config
   inbox.md                  # the 3 URLs above, unchecked
   CLAUDE.md                 # load-bearing: instruct agents to read wiki/index.md first
   raw/
     web/
     github/
     youtube/
     assets/
   wiki/
     index.md
     log.md
     overview.md
     sources/
     topics/
     syntheses/
   ```
4. Pre-install: verify `yt-dlp` is available for the YouTube step.
5. Have a notes file open — `manual-pass-findings.md` — to capture observations in real time.

---

## The pass — step by step

### Step 0 — Scaffold

- Hand-create the directory tree above.
- Write `.pin-llm-wiki.yml` with:
  ```yaml
  version: 1
  domain: "Agentic GenAI learning journey"
  detail_level: standard
  source_types: [web, github, youtube]
  ```
- Write `CLAUDE.md` with the load-bearing instructions block from `research.md §10`.
- Write `inbox.md` with the 3 URLs unchecked.
- **Commit** as baseline so we can `git diff` between stages.

### Step 1 — GitHub repo (easiest, least risky)

Start here because GitHub is the most predictable fetch.

**Fetch:**
- Read `https://github.com/obra/superpowers` — README, top-level structure, any `docs/` or `examples/`.
- Save as a single compiled `raw/github/obra-superpowers.md` (summary-style, not full clone).
- Update `raw/github/README.md` with a row for this repo.

**Ingest:**
- Create `wiki/sources/superpowers.md` — summary + citations pointing into `raw/github/obra-superpowers.md`.
- Identify 1–3 topic-worthy concepts → create `wiki/topics/<slug>.md` pages.
- Update `wiki/index.md`, `wiki/overview.md`, append to `wiki/log.md`.
- Mark `[x]` in `inbox.md`.

**Capture in findings:**
- Token count for fetch + ingest.
- Did citations feel natural or forced?
- How many wiki pages were created?
- Commit the diff.

### Step 2 — YouTube video (transcript fetch)

**Fetch:**
- `yt-dlp --write-auto-sub --sub-format vtt --skip-download --sub-lang en <url>` → VTT file.
- Convert VTT → clean markdown (strip timestamps but keep time-chunks at heading level, e.g. `## [00:05:00]`).
- Save as `raw/youtube/<video-id>-<title>.md`.
- Update `raw/youtube/README.md`.

**Ingest:**
- Create `wiki/sources/<video-slug>.md` using the "replace watching" template.
- After reading only the wiki page, can we explain what the video was about without watching? That's the acceptance bar.
- Update or create topics cross-referenced from source 1.
- Update index/overview/log. Mark `[x]`.

**Capture:**
- Did yt-dlp succeed? Quality of auto-subs?
- Fallback needed if no transcript?
- Did merging with topics from source 1 feel clean or force duplication?

### Step 3 — LangChain docs site (hardest)

**Fetch:**
- Try `WebFetch` on `https://www.langchain.com/` — inspect what comes back. Is it real content or JS skeleton?
- If skeleton: try `https://python.langchain.com/docs/introduction/` or similar docs URL. Compare results.
- If still poor: document the failure, try alternatives (Jina Reader `r.jina.ai/<url>`, Firecrawl).
- For `standard` detail: landing + docs index + ~10 key pages. Stop when enough to write the wiki page.
- Save under `raw/web/langchain.com/<page-slug>.md`.

**Ingest:**
- Create `wiki/sources/langchain.md` — the "landing page replacer" template.
- Extend existing topics (agent orchestration, tool use, RAG) from sources 1 & 2 — verify merge behavior, not duplication.
- Update index/overview/log. Mark `[x]`.

**Capture:**
- Which fetching strategy actually worked? (This is the single most important finding.)
- Token cost — likely the largest of the three.
- Did topics from sources 1 & 2 grow organically or require a taxonomy shift?

### Step 4 — Lint pass

Manually run through the lint checks from `research.md §9`:

1. Citation coverage — spot-check every factual sentence across 3 sources pages + all topic pages.
2. Contradictions — any?
3. Orphans — pages with no inbound links?
4. Data gaps — concepts mentioned but no topic page?
5. Missing cross-references — topic page mentions another known topic without linking?

Record all findings; don't fix them yet. The PRD will decide whether the linter should auto-suggest fixes.

### Step 5 — Agent-consumption test

Open a fresh Claude Code session in `agentic-ai-wiki/`. Ask:
> "What's the difference between how superpowers and LangChain approach agent tool use?"

Observe:
- Does the agent follow `CLAUDE.md` and read `wiki/index.md` first?
- Does it cite wiki page names?
- Is the answer synthesized from the wiki, or hallucinated from training data?

This is the core validation of the "wiki for both humans and agents" principle.

---

## Findings to record

Keep `manual-pass-findings.md` structured as:

```markdown
## Source 1: superpowers (GitHub)
- Fetch: [tool used, worked/failed, notes]
- Token cost fetch: X
- Token cost ingest: X
- Wiki pages created: N
- Friction points: ...
- Surprises: ...

## Source 2: youtube video
...

## Source 3: langchain
...

## Cross-cutting observations
- Topics structure — did `topics/` stay coherent across sources?
- Citation discipline — easy or hard?
- Merging — clean or messy?
- Idempotency — did we hit any partial-state issues?

## Decisions the PRD needs to make
1. ...
2. ...

## Things that surprised us
1. ...

## Risks confirmed (from §14)
- ...

## Risks that turned out to be paranoia
- ...
```

---

## Deliverables from this pass

1. `agentic-ai-wiki/` — the actual working wiki (the artifact).
2. `manual-pass-findings.md` — everything we learned.
3. Updated `research.md` — reflect real findings (move items from "Risks" to "Confirmed issues" or "Dismissed").
4. First draft of `PRD.md` — informed by all of the above.

---

## What we explicitly defer

- Init skill (we hand-scaffold this time).
- Refresh / remove workflows.
- `arxiv`, `blogs`, `threads` source types.
- Cost guard / budget enforcement.
- Auto-commit per ingest (we commit manually after each step to get clean diffs).
- Playwright / headless browser integration (evaluated only if WebFetch + Jina both fail).

---

## Guard rails

- **Stop if a single source exceeds 200k input tokens during fetch.** That's a signal we've over-scoped `standard`.
- **Stop if the LangChain fetch fails with all three strategies** (WebFetch, Jina Reader, direct docs URL). Document and move on; don't spiral on tooling.
- **If citation discipline feels impossible**, stop and rethink. That's the load-bearing principle — if it doesn't work manually, it won't work automated.

---
