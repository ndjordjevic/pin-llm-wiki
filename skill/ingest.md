# ingest — shared ingest protocol

Called by `add`, `run`, and `refresh`. Execute steps in order.

**Context passed in by the caller:**

| Variable | Value |
|---|---|
| `slug` | source identifier (e.g. `langchain-ai-langchain`, `abc123-video-title`, `docs.langchain.com`) |
| `type` | `github` / `youtube` / `web` |
| `raw_file_path` | path to the completed raw file (e.g. `raw/github/langchain-ai-langchain.md`) |
| `effective_detail_level` | resolved detail level (`brief` / `standard` / `deep`) |
| `auto_mark_complete` | from `.pin-llm-wiki.yml` |
| `today` | current date `YYYY-MM-DD` |

---

## Step 1 — Read the raw file

Read `raw_file_path` fully before writing any wiki content.

---

## Step 2 — Create or update `wiki/sources/<slug>.md`

**Frontmatter:**

```yaml
---
type: source
tags: []
related: []
detail_level: <effective_detail_level>
created: <today>
updated: <today>
---
```

If the page **already exists** (this is an update or refresh): preserve the existing `created`, `tags`, and `related` values. Always overwrite `updated` and `detail_level`.

**MUST NOT include a `sources:` field.** Source pages do not cite themselves.

**Body structure:**

1. Summary paragraph — what this source is and why it matters for the wiki's domain.
2. Banner citation: `_All claims below are sourced from ../../raw/<type>/<slug-file>.md unless otherwise noted._`
3. Sectioned body by type:
   - **GitHub:** What it does | Installation | Key features | Architecture | Example usage | Maintenance status
   - **YouTube:** What the video is about (1 paragraph — sufficient to replace watching) | Key points by chapter | Notable quotes | Speaker context
   - **Web/product:** What it does | Key features | Architecture and concepts | Main APIs | When to use | Ecosystem

Add per-paragraph inline citations only when a **second** raw file contributes to this page. The banner covers all content from the primary raw file alone.

---

## Step 3 — Do NOT create topic pages

Topic creation happens at lint time only (lint Check #4). Skip this step entirely.

---

## Step 4 — Update `wiki/index.md`

1. Read `wiki/index.md`.
2. **If a row for this slug already exists** in the Sources table: update its date column and `detail_level` column in-place (do not add a new row; do not change the count).
3. **If no row exists:** add a row to the Sources table:
   `| <slug> | <type> | <effective_detail_level> | <today> | |`
   Then find the `_N sources ingested._` line and increment N by 1.
4. Write the updated file.

---

## Step 5 — Update `wiki/overview.md`

1. Read `wiki/overview.md`. Check the `sources:` frontmatter list.

2. **If `"[[<slug>]]"` already appears in `sources:`** — this is a refresh:
   - Update the `updated:` frontmatter field to `<today>`. Do not add another paragraph or duplicate the frontmatter entry.
   - Write the updated file and stop at this step.

3. **If `sources:` is empty (`sources: []`)** — this is the first source ingested:
   - Replace the placeholder body (the `_No sources ingested yet..._` paragraph) with an opening synthesis paragraph describing what this source covers and what it contributes to understanding the domain. Cite `[[<slug>]]`.
   - Update `sources:` frontmatter to: `sources:\n  - "[[<slug>]]"`

4. **If `sources:` already has entries but does not include this slug** — extend the existing synthesis:
   - Add a new paragraph covering what the new source contributes relative to existing ones. Cite `[[<slug>]]`.
   - Append `  - "[[<slug>]]"` to the `sources:` frontmatter list.

5. Update the `updated:` frontmatter field to `<today>`.
6. Write the updated file.

---

## Step 6 — Append to `wiki/log.md`

Read `wiki/log.md`. Insert this block below the frontmatter block and the `# ... wiki — log` heading, **above** any existing `## ...` entries (newest at top):

```
## <today> | ingest | <slug> | <one-line summary from the raw file>

- Created: wiki/sources/<slug>.md
- Updated: wiki/index.md, wiki/overview.md, wiki/log.md, raw/<type>/README.md, inbox.md
```

Write the updated file.

---

## Step 7 — Update `raw/<type>/README.md`

Read `raw/<type>/README.md`.

**If a row for this slug already exists** in the Files table: update its `last-fetched` date column in-place (do not append a new row).

**If no row exists:** append one row to the Files table:
- **GitHub:** `| raw/github/<org>-<repo>.md | <org>/<repo> | <stars> | <default-branch> | <latest-release> | <today> | |`
- **YouTube:** `| raw/youtube/<video-id>-<slug>.md | <title> | <channel> | <duration> | <upload-date> | <today> | |`
- **Web:** `| raw/web/<domain>.md | <domain> | <pages-fetched> | <today> | |`

Write the updated file.

---

## Step 8 — Move inbox line

1. Read `inbox.md`.
2. Locate the URL's line under `## Pending`.
3. Append `<!-- ingested <today> -->` to the line.
4. If `auto_mark_complete: true`: flip `[ ]` → `[x]`.
5. Move the line (with the appended comment, updated checkbox) from `## Pending` to the bottom of `## Completed`.
6. Write the updated `inbox.md`.

---

## Step 9 — Git (no agent commits)

Do not run `git commit` or `git push` after ingest—see the wiki’s `AGENTS.md` **Git — never auto-commit**.
