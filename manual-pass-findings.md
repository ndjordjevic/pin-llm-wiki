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

*(fill in after completing Step 1)*

### Fetch

### Ingest

### Findings

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

