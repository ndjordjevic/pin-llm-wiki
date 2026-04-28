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

**Raw files:** read the source page's frontmatter and check whether it contains a `raw_files:` list (indicating a **unified page** — usually web + companion GitHub).

**Unified page** (`raw_files:` present): build the raw-file archive list from `raw_files:`. For each entry, strip the leading `../../` to convert it to a repo-relative path (e.g. `../../raw/github/foo-bar.md` → `raw/github/foo-bar.md`). Also check for a sibling deep-clone directory `raw/github/<companion-slug>/` and include it if present. Each listed file or directory must actually exist on disk to be archived; missing ones are noted in the report but do not block the rest.

**Non-unified page** (no `raw_files:`): check for these exact paths only (both may exist, either may be absent):
- Single file: `raw/<type>/<slug>.md`
- Deep clone directory: `raw/<type>/<slug>/` (entire directory)

Do not glob or prefix-match in either case — only the explicit paths above.

If no raw files resolve at all: note this in the report but continue — the wiki source page may still exist.

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
3. Find the `_N sources ingested._` line; decrement N by 1.
4. Write the updated file.

---

## Step 5 — Update `wiki/overview.md`

1. Read `wiki/overview.md`.
2. Remove the line `  - "[[<slug>]]"` from the `sources:` frontmatter list.
3. **Remove the body paragraph for this slug.** The overview body invariant is `len(sources) == paragraph_count` (one paragraph per entry in `sources:`, in the same order — see `ingest.md` Step 5).
   - Find the paragraph that primarily cites `[[<slug>]]` and delete it.
   - If `[[<slug>]]` is mentioned within a paragraph that primarily cites a different surviving source, just remove the `[[<slug>]]` reference (and any sentence solely about it) — do not delete the whole paragraph.
4. **Invariant check before writing:** post-edit body paragraph count must equal the new `len(sources)`. If it does not, do NOT write the file — report `"overview.md paragraph count mismatch after removing [[<slug>]]. Fix manually: paragraph count must equal len(sources)."` and stop. (At this point sub-step 2 has already removed the slug from `sources:` in your in-memory copy; bailing without writing means that change is dropped and the file on disk still contains the entry — the user must reconcile the body manually before re-running.)
5. Update the `updated:` frontmatter field to `<today>`.
6. Write the updated file.

---

## Step 6 — Move files to archive

Move (do not copy) each file/directory resolved in Step 2 to its archive destination, preserving the `raw/<type>/<filename>` substructure:
- `wiki/sources/<slug>.md` → `wiki/.archive/sources/<slug>.md`
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

Write the updated file.

---

## Step 8 — Scan for dangling references

Scan every wiki page in `wiki/sources/`, `wiki/overview.md`, `wiki/log.md` for:

1. **Broken wikilinks** — `[[<slug>]]` anywhere in body or frontmatter of a surviving page.
2. **Broken raw citations** — any path pointing into `raw/<type>/` that names one of the archived raw files (the page's own `<slug>` and, for unified pages, the companion slug derived from `raw_files:`). Catches forms like `../../raw/github/<slug>.md` and `../raw/<type>/<slug>.md`.

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
