# lint — wiki health checks (12 checks; #2 and #6 deferred)

(Skill-directory paths and the `.pin-llm-wiki.yml` Guard are defined in `SKILL.md`.)

## Setup

Read `.pin-llm-wiki.yml` → `domain`, `stale_threshold_days` (default `30`).

Discover wiki files: `wiki/sources/*.md`, `wiki/overview.md`, `wiki/log.md`, `wiki/index.md`.

Read `wiki/index.md` Sources table to build the **known-slugs set** (used by Checks #3, #4).

Initialize `findings = []`. Each finding: `{severity, check, file, line?, message}`.

---

## Check execution order

```
A — Check #7   frontmatter shape
B — Check #8   citation path format
C — Check #5   stale sources
D — Auto-fix 1 index links (overview / log)
E — Check #3   orphans
F — Check #1   citation coverage
G — Check #4   missing cross-references
H — Check #9   inbox consistency
I — Check #10  adapter sync → Auto-fix 2 (re-sync from AGENTS.md)
J — Check #11  split-product
M — Check #12  parent-child consistency
K — Check #2   contradictions       (Phase 1: deferred)
L — Check #6   terminology collisions (Phase 1: deferred)
```

---

## Step A — Check #7: Frontmatter shape (ERROR)

For each `wiki/sources/*.md`:
- `sources:` key present → ERROR: source page must not cite itself.
- Both `subpages:` and `parent_slug:` present → ERROR: cannot be both umbrella and sub.
- `subpages:` with `companion_urls:` or `raw_files:` → ERROR: umbrella cannot also be unified.
- `parent_slug:` with `companion_urls:` or `raw_files:` → ERROR: sub cannot also be unified.

For `wiki/overview.md`: missing or null `sources:` → WARN.

---

## Step B — Check #8: Citation path format (ERROR)

Scan body links pointing into `raw/`. Required prefixes:
- From `wiki/sources/` → `../../raw/`
- From `wiki/overview.md` → `../raw/`

Anything else (`raw/...`, `/raw/...`) → ERROR: root-relative or bare citation path.

---

## Step C — Check #5: Stale sources (INFO)

For each source page, if `today - updated > stale_threshold_days` → INFO: `source page last updated N days ago`.

---

## Step D — Auto-fix 1: Index links

If `wiki/index.md` body lacks `[[overview]]` or `[[log]]`, insert `→ [[overview]] | [[log]]` immediately below the `# <title>` heading. Log: `Auto-fix applied: added [[overview]] | [[log]] links to wiki/index.md`.

---

## Step E — Check #3: Orphan pages (WARN)

Build inbound-link map: every `[[wikilink]]` in body and frontmatter of every wiki page. Page P is an orphan if no other page contains `[[P-slug]]`.

Excluded: `wiki/index.md` (root, no inbound by design). Included: `overview.md`, `log.md` (must be linked from index).

---

## Step F — Check #1: Citation coverage (ERROR / WARN)

- Source pages: missing the `_All claims below are sourced from ../../raw/...` banner → ERROR.
- `wiki/overview.md`: no `[[wikilink]]` to any source page → WARN.

---

## Step G — Check #4: Missing cross-references (WARN)

For each page P, scan body for occurrences of any known-slug or its index-table title that are not already inside a `[[wikilink]]` → WARN: `page mentions '<entity>' without a [[wikilink]]`.

If a source page has empty `related: []` AND Check #4 found candidates, include that in the same finding.

Match is case-insensitive verbatim; do not infer or expand abbreviations.

---

## Step H — Check #9: Inbox consistency (WARN)

In `inbox.md`, any `- [x] ...` line under `## Pending` → WARN: `inbox line is checked but still under ## Pending`.

---

## Step I — Check #10: Adapter sync (WARN)

`AGENTS.md` is the single canonical source — Cursor, Claude Code (via `CLAUDE.md` → `@AGENTS.md`), GitHub Copilot, and Copilot CLI all load it automatically. No adapter files need syncing.

This check is now a no-op. Skip it.

---

## Step J — Check #11: Split-product source pages (WARN)

Build `product → [{slug, source_url, has_companion_urls}]` from all source pages. Skip umbrellas (page slug matches `product:` AND has `subpages:`). For multi-product subs (`parent_slug:` present), do not emit the WARN — emit INFO instead: `'<product>' has multi-product sub-page (<sub>) and separate github source (<gh>); cannot be auto-unified.`

For other products with ≥2 entries and **none** unified (no `companion_urls:`):
- Classify each entry: `source_url == https://github.com/<org>/<repo>` (with optional trailing slash) is a github source; anything else (including `github.com/.../tree/...`) is web.
- If the group has both a github source AND a web source → WARN: `split-product — '<product>' has separate web (<web-slug>) and github (<gh-slug>); /pin-llm-wiki remove <gh-slug> and re-add the web URL to consolidate.`

Not auto-fixed — consolidation is destructive.

---

## Step M — Check #12: Parent-child consistency (ERROR)

Build `umbrella_subs: umbrella_slug → set(subpages)` and `sub_parents: sub_slug → parent_slug`.

For each (umbrella, subs):
- For each listed sub: `wiki/sources/<sub>.md` must exist AND its `parent_slug:` must equal `umbrella`. Else ERROR.

For each (sub, parent):
- `wiki/sources/<parent>.md` must exist AND must list `<sub>` in `subpages:`. Else ERROR.

Pages with neither field are skipped (standalone / unified).

---

## Step K — Check #2: Contradictions (Phase 1: deferred)

Add note: `Check #2 (contradictions): deferred in Phase 1.`

## Step L — Check #6: Terminology collisions (Phase 1: deferred)

Add note: `Check #6 (terminology collisions): deferred in Phase 1.`

---

## Output report

```
Lint report — <domain> wiki
<today> | <N> sources | 12 checks

ERRORs (<count>)
  [Check #N]  <file>:<line>  <message>

WARNs (<count>)
  [Check #N]  <file>:<line>  <message>

INFOs (<count>)
  [Check #N]  <file>  <message>

Auto-fixes applied (<count>):
  - <description>

Deferred (Phase 1): Check #2 (contradictions), Check #6 (terminology collisions)

Summary: <N> ERROR, <N> WARN, <N> INFO — <N> auto-fix(es) applied
```

Omit empty severity sections (don't print "ERRORs (0)"). If no findings and no auto-fixes: print `All checks passed.`

---

No agent commits, even after auto-fixes — see SKILL.md Git policy.
