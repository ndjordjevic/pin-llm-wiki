# remove — soft-delete a source

## Guard

Check whether `.pin-llm-wiki.yml` exists in the current working directory. If not, stop:
> "No wiki found here (`.pin-llm-wiki.yml` missing). Run `/pin-llm-wiki init` to scaffold one first."

---

## Setup

Read `.pin-llm-wiki.yml` and extract: `domain`.

Set `today` = current date in `YYYY-MM-DD` format.

The slug is the first argument after `/pin-llm-wiki remove`.

---

## Step 1 — Validate slug

Read `wiki/index.md`. Check whether the slug appears in the Sources table.

If not found → stop:
> "Slug `<slug>` not found in wiki/index.md Sources table. Check the slug and try again."

Record the source `type` from the Sources table row (needed for raw file paths).

---

## Step 2 — Resolve files to archive

**Source page:** `wiki/sources/<slug>.md`

Read the source page's frontmatter and determine its shape:

| Frontmatter signal | Shape |
|---|---|
| `raw_files:` present | **Unified web+github** |
| `subpages:` present | **Multi-product umbrella** |
| `parent_slug:` present | **Multi-product sub** |
| none of the above | **Standalone** |

**Unified page** (`raw_files:` present): build the raw-file archive list from `raw_files:`. For each entry, strip the leading `../../` to convert it to a repo-relative path (e.g. `../../raw/github/foo-bar.md` → `raw/github/foo-bar.md`). Also check for a sibling deep-clone directory `raw/github/<companion-slug>/` and include it if present.

**Multi-product umbrella** (`subpages:` present): the umbrella shares **one** raw file with all its subs. The raw file is archived only when removing the umbrella, not when removing an individual sub.
- Raw archive list: just `raw/web/<slug>.md`.
- **Cascade target list:** every sub listed in `subpages:`. For each `<sub-slug>`, also archive `wiki/sources/<sub-slug>.md`. (Subs do not own raw files; the single web raw covers them.)
- All cascade targets are processed by Steps 4, 5, 6, and 7 in the same pass — they are removed from `wiki/index.md`, dropped from `wiki/overview.md`'s `sources:` and body paragraphs, moved to `wiki/.archive/sources/`, and listed in the `wiki/log.md` entry under `Archived:`.

**Multi-product sub** (`parent_slug:` present): only this sub is removed. The raw file is **kept** (it still backs the umbrella + remaining subs). Resolve files to archive: just `wiki/sources/<slug>.md`. Then run **Step 2x** below before continuing.

**Standalone page** (none of the above): check for these exact paths only (both may exist, either may be absent):
- Single file: `raw/<type>/<slug>.md`
- Deep clone directory: `raw/<type>/<slug>/` (entire directory)

Do not glob or prefix-match in any case — only the explicit paths above. Each listed file or directory must actually exist on disk to be archived; missing ones are noted in the report but do not block the rest.

If no raw files resolve at all (and the page is not a multi-product sub): note this in the report but continue — the wiki source page may still exist.

---

## Step 2x — Update umbrella when removing a sub

Runs only when the page being removed has `parent_slug:` set.

1. Read `wiki/sources/<parent_slug>.md`.
2. Remove `<slug>` from its `subpages:` list.
3. If the umbrella's body contains a `## Products` section that wikilinks `[[<slug>]]`, remove that bullet line.
4. Update the umbrella's `updated:` frontmatter field to `<today>`.
5. Write the updated file.

If `subpages:` becomes empty after removal, leave the umbrella in place but note in the report:
> `Umbrella '<parent_slug>' has no remaining sub-pages. Consider running '/pin-llm-wiki remove <parent_slug>' to clean it up.`

---

## Step 3 — Ensure archive directories exist

Create the following directories if they do not exist:
- `wiki/.archive/sources/`
- `wiki/.archive/raw/<type>/`

---

## Step 4 — Update `wiki/index.md`

Do this **before** moving files, so a partial failure leaves the filesystem consistent with the index.

1. Read `wiki/index.md`.
2. Remove the row for `<slug>` from the Sources table.
3. **Multi-product umbrella cascade:** also remove every sub-slug listed in `subpages:`.
4. Find the `_N sources ingested._` line; decrement N by the number of rows removed (1 for standalone/unified/sub; `1 + len(subpages)` for an umbrella cascade).
5. Write the updated file.

---

## Step 5 — Update `wiki/overview.md`

1. Read `wiki/overview.md`.
2. Build the **removal set** of slugs:
   - Standalone / unified / sub: just `<slug>`.
   - Multi-product umbrella cascade: `<slug>` + every entry in `subpages:`.
3. For each slug in the removal set:
   a. Remove its `  - "[[<slug>]]"` line from the `sources:` frontmatter list.
   b. Find the paragraph that primarily cites `[[<slug>]]` and delete it. If `[[<slug>]]` only appears within a paragraph that primarily cites a different surviving source, just remove the `[[<slug>]]` reference (and any sentence solely about it) — do not delete the whole paragraph.
4. **Invariant check before writing:** post-edit body paragraph count must equal the new `len(sources)`. The overview body invariant is `len(sources) == paragraph_count` (one paragraph per entry in `sources:`, in the same order — see `ingest.md` Step 5). If the count does not match, do NOT write the file — report `"overview.md paragraph count mismatch after removing <removal-set>. Fix manually: paragraph count must equal len(sources)."` and stop.
5. Update the `updated:` frontmatter field to `<today>`.
6. Write the updated file.

---

## Step 6 — Move files to archive

Move (do not copy) each file/directory resolved in Step 2 to its archive destination, preserving the `raw/<type>/<filename>` substructure:
- `wiki/sources/<slug>.md` → `wiki/.archive/sources/<slug>.md`
- **Multi-product umbrella cascade:** for each sub in `subpages:`, also move `wiki/sources/<sub-slug>.md` → `wiki/.archive/sources/<sub-slug>.md`.
- For each resolved `raw/<type>/<file-or-dir>`: → `wiki/.archive/raw/<type>/<file-or-dir>` (create `wiki/.archive/raw/<type>/` if it does not yet exist for that type — Step 3 only created the directory for the page's own `<type>`; unified pages may add a second type).

---

## Step 7 — Append to `wiki/log.md`

Read `wiki/log.md`. Insert below the heading (newest at top):

```
## <today> | remove | <slug> | soft-deleted

- Archived: wiki/sources/<slug>.md → wiki/.archive/sources/<slug>.md
- Archived: raw/<type>/<slug-file(s)> → wiki/.archive/raw/<type>/
- Updated: wiki/index.md, wiki/overview.md, wiki/log.md
```

For a **multi-product umbrella cascade**, expand the entry:

```
## <today> | remove | <slug> | umbrella + <N> sub-pages soft-deleted

- Archived: wiki/sources/<slug>.md, wiki/sources/<slug>-<sub1>.md, wiki/sources/<slug>-<sub2>.md, ... → wiki/.archive/sources/
- Archived: raw/web/<slug>.md → wiki/.archive/raw/web/
- Updated: wiki/index.md, wiki/overview.md, wiki/log.md
```

For a **multi-product sub** removal, also note that the umbrella was updated:

```
## <today> | remove | <slug> | sub-page soft-deleted (raw kept; umbrella updated)

- Archived: wiki/sources/<slug>.md → wiki/.archive/sources/<slug>.md
- Updated: wiki/sources/<parent_slug>.md (subpages list), wiki/index.md, wiki/overview.md, wiki/log.md
```

Write the updated file.

---

## Step 8 — Scan for dangling references

Build the **archived-slugs set**: the slug being removed plus every cascaded sub-slug (for an umbrella) plus every companion slug derived from `raw_files:` (for a unified page).

Scan every wiki page in `wiki/sources/`, `wiki/overview.md`, `wiki/log.md` for:

1. **Broken wikilinks** — `[[<archived-slug>]]` anywhere in body or frontmatter of a surviving page.
2. **Broken raw citations** — any path pointing into `raw/<type>/` that names one of the archived raw files. Catches forms like `../../raw/github/<slug>.md` and `../raw/<type>/<slug>.md`.

Collect all matches as `{file, line, match}` and present them in the report below. Do not auto-fix.

---

## Step 9 — Git (no agent commits)

Do not run `git commit` or `git push` after remove—see the wiki’s `AGENTS.md` **Git — never auto-commit**.

---

## Output report

```
Removed: <slug>

  Archived:    wiki/sources/<slug>.md → wiki/.archive/sources/<slug>.md
               raw/<type>/<slug-file(s)> → wiki/.archive/raw/<type>/
  Updated:     wiki/index.md (-1 source), wiki/overview.md, wiki/log.md
  (Do not commit; human commits when ready.)

Dangling references found (<N>):
  <file>:<line>  <match>
  ...

[No dangling references found.]   ← if none
```

Fix dangling references manually (update or remove the wikilinks and citations in the listed pages), then run `/pin-llm-wiki lint` for full wiki validation.

**To undo:** files are in `wiki/.archive/`. Move them back to their original paths, restore the index.md row, re-add the overview.md frontmatter entry and body paragraph, and revert the log entry manually.
