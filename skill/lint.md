# lint — wiki health checks

## Guard

Check whether `.pin-llm-wiki.yml` exists in the current working directory. If not, stop:
> "No wiki found here (`.pin-llm-wiki.yml` missing). Run `/pin-llm-wiki init` to scaffold one first."

---

## Setup

**Read config:**
Read `.pin-llm-wiki.yml` and extract: `domain`, `stale_threshold_days`, `topic_creation` (default: `report`), `topic_min_products` (default: `3`).

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
Step L  — Check #11  (adapter sync)  →  Auto-fix 3 (re-sync adapters from AGENTS.md)
Step M  — Check #12  (split-product source pages)
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

## Step H — Check #4: Data gaps (INFO)

**Concept extraction:**
Read each source page body. Extract **capitalized multi-word phrases** (e.g. "Tool Calling", "Vector Store", "Agent Loop") that:
- Appear in headings or as bold terms (`**...**`)
- Are not themselves a page slug

Build a concept-frequency map: `concept → set of source slugs that mention it`.

**Count unique products, not unique sources.** For each source mentioning the concept, read its `product:` frontmatter field. Sources sharing a non-null `product:` value count as **one** product. Sources with `product: null` each count as their own product. The "unique product count" for a concept = `|{ product values + null-product source slugs }|`.

For each concept whose unique-product count is **≥ `topic_min_products`** (default 3) and that has no corresponding topic page in `wiki/topics/`:

→ `INFO: data gap — '<concept>' appears in N products (sources: <slug list, deduplicated by product>); consider promoting to a topic page via the manual harvest flow (see AGENTS.md).`

Concepts that appear in fewer than `topic_min_products` distinct products are not reported (avoids noise from per-product feature names like a single product's marketing site + GitHub repo).

**Topic creation behavior** depends on the `topic_creation` config value:

- `report` (default) — **report only**. Findings are listed under "Topic candidates" in the lint output. The human runs the manual harvest flow (AGENTS.md "Manual harvest") to promote a candidate to a real topic page with body content.
- `auto-stub` (legacy) — for each candidate also create `wiki/topics/<concept-slug>.md` (concept-slug: lowercase, spaces to hyphens) with this stub:
  ```yaml
  ---
  type: topic
  tags: []
  sources:
    - "[[source-slug-1]]"
    - "[[source-slug-2]]"
    - "[[source-slug-3]]"
  related: []
  created: YYYY-MM-DD
  updated: YYYY-MM-DD
  ---
  ```
  Body:
  ```
  # <Concept Name>

  _Stub generated by lint on YYYY-MM-DD. Concept appears in: [[source-slug-1]], [[source-slug-2]], [[source-slug-3]]. Body left for human or next `add` to fill._
  ```
  Then update `wiki/index.md`:
  - If a Topics table exists: append `| [[<concept-slug>]] | <source-slugs joined by ", "> | <today> |`
  - If no Topics table exists yet: replace the `_No topic pages yet..._` placeholder with a table:
    ```
    | Slug | Sources | Created |
    |---|---|---|
    | [[<concept-slug>]] | <source-slugs joined by ", "> | <today> |
    ```
  Log each fix:
  > `Auto-fix applied: created stub wiki/topics/<concept-slug>.md and added index row (concept '<Concept>' in N products)`

`auto-stub` is kept for backwards compatibility but not recommended — empty stubs add navigation cost without information value.

---

## Step I — Check #10: Inbox consistency (WARN)

Read `inbox.md`. Scan the `## Pending` section for lines matching:
- `- [x] ...` (checked checkbox)

Any checked line under `## Pending` → `WARN: inbox line is checked [x] but still under ## Pending (should be under ## Completed or the checkbox should be [ ])`.

---

## Step L — Check #11: Adapter sync (WARN) → Auto-fix 3

The wiki ships agent instructions to multiple AI tools via three files derived from one canonical body:

| File | Role |
|---|---|
| `AGENTS.md` | canonical source (Claude Code reads it via `CLAUDE.md` → `@AGENTS.md`) |
| `.cursor/rules/wiki-instructions.mdc` | Cursor adapter — Cursor frontmatter + AGENTS.md body |
| `.github/copilot-instructions.md` | GitHub Copilot adapter — AGENTS.md body verbatim |

Drift between these files means the three tools behave differently in the same wiki — exactly the problem the multi-adapter design exists to prevent.

**Check:** if either adapter file's body (after stripping the leading YAML frontmatter from the `.mdc`, if any) does not byte-match `AGENTS.md` → `WARN: adapter file <path> is out of sync with AGENTS.md`.

**Auto-fix 3:** rewrite the drifted adapter file from `AGENTS.md`:
- `.github/copilot-instructions.md` ← contents of `AGENTS.md` verbatim.
- `.cursor/rules/wiki-instructions.mdc` ← preserve its existing top-of-file YAML frontmatter block (the `---` … `---` block before the first heading); replace everything after with the contents of `AGENTS.md`. If no frontmatter exists, prepend the standard one:
  ```
  ---
  description: Agent instructions for the <domain> wiki (always-on)
  alwaysApply: true
  ---
  ```

Log each fix:
> `Auto-fix applied: re-synced <path> from AGENTS.md`

If the wiki is missing one of the adapter files entirely (e.g. a Copilot-only wiki has no `.cursor/`), skip — do not create the missing adapter.

---

## Step M — Check #12: Split-product source pages (WARN)

Scan all source pages in `wiki/sources/*.md`. For each page read its `product:` and `source_url:` frontmatter fields. Build a map: `product → list of {slug, source_url}`.

For each product that has **2 or more entries** in the map and whose entries all **lack a `companion_urls:` field** (i.e. none have been unified yet):
- If the group contains **at least one web source** (source_url does NOT start with `https://github.com`) AND **at least one github source** (source_url starts with `https://github.com`):
  → `WARN: split-product — '<product>' has separate web source page (<web-slug>) and github source page (<github-slug>); the unified ingestion flow now produces a single source page per product. To consolidate, /pin-llm-wiki remove <github-slug> and re-add the web URL with /pin-llm-wiki run (the companion fetch will pick up the GitHub repo automatically).`

Severity: WARN. Not auto-fixed — consolidation is destructive; requires human action.

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
<today> | <N> sources | 12 checks

ERRORs (<count>)
  [Check #N]  <file>:<line>  <message>
  ...

WARNs (<count>)
  [Check #N]  <file>:<line>  <message>
  ...

INFOs (<count>)
  [Check #N]  <file>  <message>
  ...

Topic candidates (<count>)
  '<Concept Name>'  ([[slug-1]], [[slug-2]], [[slug-3]])
  ...

Auto-fixes applied (<count>):
  - <description of each fix>

Deferred (Phase 1): Check #2 (contradictions), Check #7 (terminology collisions)

Summary: <N> ERROR, <N> WARN, <N> INFO — <N> auto-fix(es) applied
```

If there are no findings in a severity category, omit that section from the output (do not print "ERRORs (0)"). Same applies to "Topic candidates" — omit when none.

If there are no findings at all and no auto-fixes: print `All checks passed.`

---

## Git (no agent commits)

Do not run `git commit` or `git push` after lint, even if auto-fixes were applied—see the wiki’s `AGENTS.md` **Git — never auto-commit**.
