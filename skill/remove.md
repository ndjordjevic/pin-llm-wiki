# remove — soft-delete a source

## Guard

Check whether `.pin-llm-wiki.yml` exists in the current working directory. If not, stop:
> "No wiki found here (`.pin-llm-wiki.yml` missing). Run `/pin-llm-wiki init` to scaffold one first."

---

## Setup

Read `.pin-llm-wiki.yml` and extract: `domain`, `auto_commit`.

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

**Raw files:** check for these exact paths only (both may exist, either may be absent):
- Single file: `raw/<type>/<slug>.md`
- Deep clone directory: `raw/<type>/<slug>/` (entire directory)

Do not glob or prefix-match — only these two exact paths.

If neither raw path exists: note this in the report but continue — the wiki source page may still exist.

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
3. Leave the body paragraph(s) citing `[[<slug>]]` in place — those are human prose and are flagged in Step 7.
4. Update the `updated:` frontmatter field to `<today>`.
5. Write the updated file.

---

## Step 6 — Move files to archive

Move (do not copy) each resolved file/directory to its archive destination:
- `wiki/sources/<slug>.md` → `wiki/.archive/sources/<slug>.md`
- `raw/<type>/<slug>.md` → `wiki/.archive/raw/<type>/<slug>.md`
- `raw/<type>/<slug>/` → `wiki/.archive/raw/<type>/<slug>/`

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

Scan every wiki page in `wiki/sources/`, `wiki/topics/`, `wiki/syntheses/`, `wiki/overview.md`, `wiki/log.md` for:

1. **Broken wikilinks** — `[[<slug>]]` anywhere in body or frontmatter of a surviving page.
2. **Broken raw citations** — any path containing `<slug>` pointing into `raw/<type>/` (e.g. `../../raw/github/<slug>.md` or `../raw/<type>/<slug>.md`).

Collect all matches as `{file, line, match}` and present them in the report below. Do not auto-fix.

---

## Step 9 — Git commit (if `auto_commit: true`)

```
git add -A wiki/ raw/
git commit -m "remove: <slug>"
```

Using `git add -A` captures both the deleted paths (wiki/sources, raw/) and the updated files (index.md, overview.md, log.md, .archive/).

---

## Output report

```
Removed: <slug>

  Archived:    wiki/sources/<slug>.md → wiki/.archive/sources/<slug>.md
               raw/<type>/<slug-file(s)> → wiki/.archive/raw/<type>/
  Updated:     wiki/index.md (-1 source), wiki/overview.md, wiki/log.md
  [Committed:  "remove: <slug>"]   ← if auto_commit: true

Dangling references found (<N>):
  <file>:<line>  <match>
  ...

[No dangling references found.]   ← if none
```

Fix dangling references manually (update or remove the wikilinks and citations in the listed pages), then run `/pin-llm-wiki lint` to verify the wiki is clean.

**To undo:** files are in `wiki/.archive/`. Move them back to their original paths, restore the index.md row, re-add the overview.md frontmatter entry, and revert the log entry manually.
