# lint — wiki health checks

## Guard

Check whether `.pin-llm-wiki.yml` exists in the current working directory. If not, stop:
> "No wiki found here (`.pin-llm-wiki.yml` missing). Run `/pin-llm-wiki init` to scaffold one first."

---

## Setup

**Read config:**
Read `.pin-llm-wiki.yml` and extract: `domain`, `stale_threshold_days`, `auto_commit`.

**Discover wiki files:**

| File set | Path pattern |
|---|---|
| Source pages | `wiki/sources/*.md` |
| Topic pages | `wiki/topics/*.md` (exclude `.gitkeep`) |
| Synthesis pages | `wiki/syntheses/*.md` (exclude `.gitkeep`) |
| Overview | `wiki/overview.md` |
| Log | `wiki/log.md` |
| Index | `wiki/index.md` |

Read `wiki/index.md` to get the canonical list of known slugs (Sources table). Build a **known-slugs set** from that table — used by Checks #3, #4, #5.

**Initialize findings list** (empty). Findings are appended as: `{severity, check, file, line?, message}`.

---

## Check execution order

Run checks in this order. Auto-fixes are applied mid-sequence (before the checks they affect):

```
Step A  — Check #8   (frontmatter shape)
Step B  — Check #9   (citation path format)
Step C  — Check #6   (stale sources)
Step D  — Auto-fix 1  (index links: overview.md / log.md)
Step E  — Check #3   (orphans)
Step F  — Check #1   (citation coverage)
Step G  — Check #5   (missing cross-references)
Step H  — Check #4   (data gaps)  →  Auto-fix 2 (topic stubs)
Step I  — Check #10  (inbox consistency)
Step J  — Check #2   (contradictions) — Phase 1: deferred
Step K  — Check #7   (terminology collisions) — Phase 1: deferred
```

---

## Step A — Check #8: Frontmatter shape (ERROR)

For each **source page** (`wiki/sources/*.md`):
1. Read its YAML frontmatter.
2. If it contains a `sources:` key → `ERROR: source page has 'sources:' frontmatter (source pages must not cite themselves)`.

For each **topic or synthesis page** (`wiki/topics/*.md`, `wiki/syntheses/*.md`):
1. If its frontmatter is missing `sources:` entirely, or `sources:` is `null` → `WARN: topic/synthesis page has no 'sources:' field`.

---

## Step B — Check #9: Citation path format (ERROR)

For each wiki page in `wiki/sources/`, `wiki/topics/`, `wiki/syntheses/`, `wiki/overview.md`:

Scan the body for any link that points into `raw/` (looks like `raw/`, `/raw/`, `../raw/`, or `../../raw/`).

Valid path prefixes by location:
- From `wiki/sources/` → must start with `../../raw/`
- From `wiki/topics/` or `wiki/syntheses/` → must start with `../raw/`
- From `wiki/overview.md` → must start with `../raw/` (if any direct raw links exist; normally overview cites source pages instead)

Flag any path that uses `/raw/...` (root-relative) or `raw/...` (no `../`) → `ERROR: root-relative or bare citation path`.

---

## Step C — Check #6: Stale sources (INFO)

For each source page in `wiki/sources/*.md`:
1. Read the `updated:` frontmatter field.
2. Compare to today's date. If the difference exceeds `stale_threshold_days` → `INFO: source page last updated N days ago (threshold: stale_threshold_days)`.

---

## Step D — Auto-fix 1: Index links

Read `wiki/index.md`. Check whether the body contains:
- A `[[overview]]` wikilink
- A `[[log]]` wikilink

If either is missing, add the line `→ [[overview]] | [[log]]` immediately below the `# <title>` heading. Log the fix:
> `Auto-fix applied: added [[overview]] | [[log]] links to wiki/index.md`

---

## Step E — Check #3: Orphan pages (WARN)

Build an **inbound-link map**: for every wiki page (sources, topics, syntheses, overview, log, index), collect all `[[wikilink]]` and `[[slug]]` references found in its body and frontmatter.

For each wiki page P:
- If no other wiki page contains `[[P-slug]]` anywhere (body or frontmatter `sources:` list) → `WARN: orphan page — no inbound wikilinks from any wiki page`.

Note: `wiki/index.md` is excluded from the orphan check (it is the root and has no inbound links by design). `wiki/overview.md` and `wiki/log.md` are **included** — they should be linked from `wiki/index.md` (the auto-fix in Step D ensures this for a healthy wiki; if they still appear as orphans after Step D, flag them).

---

## Step F — Check #1: Citation coverage (ERROR or WARN)

**Source pages** (`wiki/sources/*.md`):
Scan the body for a banner citation line matching the pattern:
`_All claims below are sourced from ../../raw/...`
If the banner is absent → `ERROR: no banner citation on source page`.

**Topic and synthesis pages** (`wiki/topics/*.md`, `wiki/syntheses/*.md`):
1. Check `sources:` frontmatter is non-empty. If empty → `ERROR: topic/synthesis page has empty sources: frontmatter`.
2. Scan the body for at least one inline raw-file citation (a path containing `../raw/`). If none found → `WARN: topic/synthesis page has no inline raw-file citations`.

**`wiki/overview.md`:**
Scan the body for at least one `[[wikilink]]` to a source page. If none found → `WARN: overview.md has no [[source page]] wikilinks` (WARN only, per §5.4).

---

## Step G — Check #5: Missing cross-references (WARN)

For each wiki page P:
1. Build the set of **wiki-known entities**: the slug and any alias (the human-readable title from the sources table in `wiki/index.md`).
2. Scan P's body text for occurrences of any known entity name that do **not** already appear inside a `[[wikilink]]`.
3. If found → `WARN: page mentions '<entity>' without a [[wikilink]] (consider linking to [[<slug>]])`.

Also: if a source page has `related: []` (empty) but Check #5 found cross-reference candidates → include that in the same finding.

Limit to entities appearing verbatim in the body text (case-insensitive match against slug or index title). Do not infer or expand abbreviations.

---

## Step H — Check #4: Data gaps (INFO) → Auto-fix 2

**Concept extraction:**
Read each source page body. Extract **capitalized multi-word phrases** (e.g. "Tool Calling", "Vector Store", "Agent Loop") that:
- Appear in headings or as bold terms (`**...**`)
- Are not themselves a page slug

Build a concept-frequency map: `concept → set of source slugs that mention it`.

For each concept appearing in **2 or more** source pages with no corresponding topic page in `wiki/topics/` → `INFO: data gap — '<concept>' mentioned in N source pages, no topic page exists`.

**Auto-fix 2 — topic stubs:**
For each data-gap concept, create `wiki/topics/<concept-slug>.md`. Derive concept-slug: lowercase, spaces to hyphens.

Stub content:
```yaml
---
type: topic
tags: []
sources:
  - "[[source-slug-1]]"
  - "[[source-slug-2]]"
related: []
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```
Body:
```
# <Concept Name>

_Stub generated by lint on YYYY-MM-DD. Concept appears in: [[source-slug-1]], [[source-slug-2]]. Body left for human or next `add` to fill._
```

Log each fix:
> `Auto-fix applied: created stub wiki/topics/<concept-slug>.md (concept '<Concept>' in N sources)`

---

## Step I — Check #10: Inbox consistency (WARN)

Read `inbox.md`. Scan the `## Pending` section for lines matching:
- `- [x] ...` (checked checkbox)

Any checked line under `## Pending` → `WARN: inbox line is checked [x] but still under ## Pending (should be under ## Completed or the checkbox should be [ ])`.

---

## Step J — Check #2: Contradictions (Phase 1: deferred)

No findings generated. Add one note to the report:
> `Check #2 (contradictions): deferred in Phase 1.`

---

## Step K — Check #7: Terminology collisions (Phase 1: deferred)

No findings generated. Add one note to the report:
> `Check #7 (terminology collisions): deferred in Phase 1.`

---

## Output report

Print the full lint report in this format:

```
Lint report — <domain> wiki
<today> | <N> sources | 10 checks

ERRORs (<count>)
  [Check #N]  <file>:<line>  <message>
  ...

WARNs (<count>)
  [Check #N]  <file>:<line>  <message>
  ...

INFOs (<count>)
  [Check #N]  <file>  <message>
  ...

Auto-fixes applied (<count>):
  - <description of each fix>

Deferred (Phase 1): Check #2 (contradictions), Check #7 (terminology collisions)

Summary: <N> ERROR, <N> WARN, <N> INFO — <N> auto-fix(es) applied
```

If there are no findings in a severity category, omit that section from the output (do not print "ERRORs (0)").

If there are no findings at all and no auto-fixes: print `All checks passed.`

---

## Git commit (if `auto_commit: true`)

If any auto-fixes were applied and `auto_commit: true`:
```
git add wiki/index.md wiki/topics/<new-stubs...>
git commit -m "lint: auto-fix — <summary of fixes applied>"
```
