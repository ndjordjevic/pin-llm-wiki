# lint — wiki health checks (12 checks; #2 and #6 deferred)

## Guard

Check whether `.pin-llm-wiki.yml` exists in the current working directory. If not, stop:
> "No wiki found here (`.pin-llm-wiki.yml` missing). Run `/pin-llm-wiki init` to scaffold one first."

---

## Setup

**Read config:**
Read `.pin-llm-wiki.yml` and extract: `domain`, `stale_threshold_days` (default: `30`).

**Discover wiki files:**

| File set | Path pattern |
|---|---|
| Source pages | `wiki/sources/*.md` |
| Overview | `wiki/overview.md` |
| Log | `wiki/log.md` |
| Index | `wiki/index.md` |

Read `wiki/index.md` to get the canonical list of known slugs (Sources table). Build a **known-slugs set** from that table — used by Checks #3 and #4.

**Initialize findings list** (empty). Findings are appended as: `{severity, check, file, line?, message}`.

---

## Check execution order

Run checks in this order. Auto-fixes are applied mid-sequence (before the checks they affect):

```
Step A  — Check #7   (frontmatter shape)
Step B  — Check #8   (citation path format)
Step C  — Check #5   (stale sources)
Step D  — Auto-fix 1 (index links: overview.md / log.md)
Step E  — Check #3   (orphans)
Step F  — Check #1   (citation coverage)
Step G  — Check #4   (missing cross-references)
Step H  — Check #9   (inbox consistency)
Step I  — Check #10  (adapter sync) → Auto-fix 2 (re-sync adapters from AGENTS.md)
Step J  — Check #11  (split-product source pages)
Step M  — Check #12  (parent-child consistency: umbrella subpages ↔ sub parent_slug)
Step K  — Check #2   (contradictions) — Phase 1: deferred
Step L  — Check #6   (terminology collisions) — Phase 1: deferred
```

---

## Step A — Check #7: Frontmatter shape (ERROR)

For each **source page** (`wiki/sources/*.md`):
1. Read its YAML frontmatter.
2. If it contains a `sources:` key → `ERROR: source page has 'sources:' frontmatter (source pages must not cite themselves)`.
3. **Multi-product mutual-exclusion checks:**
   - If both `subpages:` and `parent_slug:` are present → `ERROR: source page cannot be both an umbrella ('subpages:') and a sub ('parent_slug:')`.
   - If `subpages:` is present but `companion_urls:` or `raw_files:` is also present → `ERROR: multi-product umbrella cannot also be a unified web+github page (drop 'companion_urls:'/'raw_files:' or remove and re-add)`.
   - If `parent_slug:` is present but `companion_urls:` or `raw_files:` is also present → `ERROR: multi-product sub cannot also be a unified web+github page`.

For **`wiki/overview.md`**:
1. Read its YAML frontmatter.
2. If `sources:` is missing entirely, or `sources:` is `null` → `WARN: overview.md has no 'sources:' field`.

---

## Step B — Check #8: Citation path format (ERROR)

For each wiki page in `wiki/sources/` and `wiki/overview.md`:

Scan the body for any link that points into `raw/` (looks like `raw/`, `/raw/`, `../raw/`, or `../../raw/`).

Valid path prefixes by location:
- From `wiki/sources/` → must start with `../../raw/`
- From `wiki/overview.md` → must start with `../raw/` (if any direct raw links exist; normally overview cites source pages instead)

Flag any path that uses `/raw/...` (root-relative) or `raw/...` (no `../`) → `ERROR: root-relative or bare citation path`.

---

## Step C — Check #5: Stale sources (INFO)

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

Build an **inbound-link map**: for every wiki page (sources, overview, log, index), collect all `[[wikilink]]` and `[[slug]]` references found in its body and frontmatter.

For each wiki page P:
- If no other wiki page contains `[[P-slug]]` anywhere (body or frontmatter `sources:` list) → `WARN: orphan page — no inbound wikilinks from any wiki page`.

Note: `wiki/index.md` is excluded from the orphan check (it is the root and has no inbound links by design). `wiki/overview.md` and `wiki/log.md` are **included** — they should be linked from `wiki/index.md`.

---

## Step F — Check #1: Citation coverage (ERROR or WARN)

**Source pages** (`wiki/sources/*.md`):
Scan the body for a banner citation line matching the pattern:
`_All claims below are sourced from ../../raw/...`
If the banner is absent → `ERROR: no banner citation on source page`.

**`wiki/overview.md`:**
Scan the body for at least one `[[wikilink]]` to a source page. If none found → `WARN: overview.md has no [[source page]] wikilinks`.

---

## Step G — Check #4: Missing cross-references (WARN)

For each wiki page P:
1. Build the set of **wiki-known entities**: the slug and any alias (the human-readable title from the Sources table in `wiki/index.md`).
2. Scan P's body text for occurrences of any known entity name that do **not** already appear inside a `[[wikilink]]`.
3. If found → `WARN: page mentions '<entity>' without a [[wikilink]] (consider linking to [[<slug>]])`.

Also: if a source page has `related: []` (empty) but Check #4 found cross-reference candidates → include that in the same finding.

Limit to entities appearing verbatim in the body text (case-insensitive match against slug or index title). Do not infer or expand abbreviations.

---

## Step H — Check #9: Inbox consistency (WARN)

Read `inbox.md`. Scan the `## Pending` section for lines matching:
- `- [x] ...` (checked checkbox)

Any checked line under `## Pending` → `WARN: inbox line is checked [x] but still under ## Pending (should be under ## Completed or the checkbox should be [ ])`.

---

## Step I — Check #10: Adapter sync (WARN) → Auto-fix 2

The wiki ships agent instructions to multiple AI tools via three files derived from one canonical body:

| File | Role |
|---|---|
| `AGENTS.md` | canonical source (Claude Code reads it via `CLAUDE.md` → `@AGENTS.md`) |
| `.cursor/rules/wiki-instructions.mdc` | Cursor adapter — Cursor frontmatter + AGENTS.md body |
| `.github/copilot-instructions.md` | GitHub Copilot adapter — AGENTS.md body verbatim |

**Check:** if either adapter file's body (after stripping the leading YAML frontmatter from the `.mdc`, if any) does not byte-match `AGENTS.md` → `WARN: adapter file <path> is out of sync with AGENTS.md`.

**Auto-fix 2:** rewrite the drifted adapter file from `AGENTS.md`:
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

If the wiki is missing one of the adapter files entirely, skip — do not create the missing adapter.

---

## Step J — Check #11: Split-product source pages (WARN)

Scan all source pages in `wiki/sources/*.md`. For each page read its `product:` and `source_url:` frontmatter fields. Build a map: `product → list of {slug, source_url}`.

**Skip umbrella + sub pairs.** A multi-product umbrella page's `product:` is the umbrella slug itself (e.g. `langchain.com`); each sub uses its own product slug (e.g. `langgraph`). They never collide. If during scanning you encounter a page whose `product:` matches its own slug AND that page has a `subpages:` field, treat it as an umbrella and exclude it from collision counting against any sub.

**Skip multi-product subs entirely from the split-product warning.** Multi-product sub-pages (those with `parent_slug:`) cannot be unified — their structure is owned by the umbrella's single raw file, and the unified flow's "remove + re-add" remediation does not apply. If a sub's `product:` collides with a separately-ingested github source page (e.g. user later ingests `github.com/langchain-ai/langgraph` standalone after a multi-product langchain.com ingest), do **not** emit the standard split-product warning. Instead emit `INFO: '<product>' has a multi-product sub-page (<sub-slug>) and a separate github source (<github-slug>); these cannot be auto-unified — they coexist by design.`

For each product that has **2 or more entries** in the map and whose entries all **lack a `companion_urls:` field** (i.e. none have been unified yet):
- Classify each entry by `source_url`:
  - **github source** — `source_url` matches exactly `https://github.com/<org>/<repo>` (or with a trailing `/`) — i.e. a repo root with no extra path segments. GitHub non-root URLs (`/tree/...`, `/blob/...`, etc.) are web sources, not github sources, even though they live on `github.com`.
  - **web source** — anything else.
- If the group contains **at least one web source** AND **at least one github source**:
  → `WARN: split-product — '<product>' has separate web source page (<web-slug>) and github source page (<github-slug>); the unified ingestion flow now produces a single source page per product. To consolidate, /pin-llm-wiki remove <github-slug> and re-add the web URL with /pin-llm-wiki run (the companion fetch will pick up the GitHub repo automatically).`

Severity: WARN. Not auto-fixed — consolidation is destructive; requires human action.

---

## Step M — Check #12: Parent-child consistency (ERROR)

Scan all source pages and build two maps:

1. **`umbrella_subs`**: for each page with `subpages:`, collect `umbrella_slug → set(sub_slugs)`.
2. **`sub_parents`**: for each page with `parent_slug:`, collect `sub_slug → parent_slug`.

For each `(umbrella, subs)` in `umbrella_subs`:
- For each `<sub-slug>` listed in `subpages:`: the file `wiki/sources/<sub-slug>.md` must exist AND its `parent_slug:` must equal `umbrella`. If missing → `ERROR: umbrella '<umbrella>' lists sub-page '<sub-slug>' but wiki/sources/<sub-slug>.md does not exist`. If `parent_slug:` differs or is absent → `ERROR: umbrella '<umbrella>' lists '<sub-slug>' but its parent_slug is '<actual>'`.

For each `(sub, parent)` in `sub_parents`:
- The file `wiki/sources/<parent>.md` must exist AND its `subpages:` list must contain `<sub>`. If missing → `ERROR: sub-page '<sub>' references parent '<parent>' but wiki/sources/<parent>.md does not exist`. If `<sub>` is not in `subpages:` → `ERROR: sub-page '<sub>' references parent '<parent>' but is not listed in its subpages`.

Pages with neither `subpages:` nor `parent_slug:` are skipped — they are standalone or unified, not part of a multi-product family.

---

## Step K — Check #2: Contradictions (Phase 1: deferred)

No findings generated. Add one note to the report:
> `Check #2 (contradictions): deferred in Phase 1.`

---

## Step L — Check #6: Terminology collisions (Phase 1: deferred)

No findings generated. Add one note to the report:
> `Check #6 (terminology collisions): deferred in Phase 1.`

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

Auto-fixes applied (<count>):
  - <description of each fix>

Deferred (Phase 1): Check #2 (contradictions), Check #6 (terminology collisions)

Summary: <N> ERROR, <N> WARN, <N> INFO — <N> auto-fix(es) applied
```

If there are no findings in a severity category, omit that section from the output (do not print "ERRORs (0)").

If there are no findings at all and no auto-fixes: print `All checks passed.`

---

## Git (no agent commits)

Do not run `git commit` or `git push` after lint, even if auto-fixes were applied—see the wiki’s `AGENTS.md` **Git — never auto-commit**.
