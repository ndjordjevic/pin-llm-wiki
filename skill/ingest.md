# ingest — shared ingest protocol

Called by `add`, `run`, and `refresh`. Execute steps in order.

**Context passed in by the caller:**

| Variable | Value |
|---|---|
| `slug` | source identifier (e.g. `langchain-ai-langchain`, `abc123-video-title`, `docs.langchain.com`, `modelcontextprotocol-servers-tree-main-src-sequentialthinking`) |
| `type` | `github` / `youtube` / `web` |
| `raw_file_path` | path to the completed raw file (e.g. `raw/github/langchain-ai-langchain.md`, `raw/web/modelcontextprotocol-servers-tree-main-src-sequentialthinking.md`) |
| `effective_detail_level` | resolved detail level (`brief` / `standard` / `deep`) |
| `auto_mark_complete` | from `.pin-llm-wiki.yml` |
| `today` | current date `YYYY-MM-DD` |
| `companion_slug` | `<org>-<repo>` if a companion GitHub repo was fetched; `null` otherwise |
| `companion_raw_file_path` | `raw/github/<org>-<repo>.md` if companion fetch succeeded; `null` otherwise |

---

## Step 1 — Read the raw file(s)

Read `raw_file_path` fully before writing any wiki content.

If `companion_raw_file_path` is non-null: also read it fully. Hold both in memory. The companion raw file supplies content for the github-sourced sections of the unified source page.

---

## Step 2 — Create or update `wiki/sources/<slug>.md`

**Frontmatter:**

```yaml
---
type: source
source_url: <original URL of the source — GitHub repo URL, website URL, YouTube video URL>
companion_urls:              # ONLY on unified web+github pages; omit entirely on all others
  - https://github.com/<org>/<repo>
raw_files:                   # ONLY on unified web+github pages; omit entirely on all others
  - ../../raw/web/<domain>.md
  - ../../raw/github/<org>-<repo>.md
tags: []
related: []
product: <product-slug>
detail_level: <effective_detail_level>
created: <today>
updated: <today>
---
```

`source_url:` is the canonical URL of the source (e.g. `https://github.com/org/repo`, `https://example.com`, `https://youtube.com/watch?v=ID`). Always populated.

`product:` is a short kebab-case identifier for the product or project this source describes (e.g. `cabinet`, `gsd`, `superpowers`, `claude-memory-compiler`). Derive from the repo/site name — strip the author prefix from GitHub slugs (e.g. `obra-superpowers` → `superpowers`, `coleam00-claude-memory-compiler` → `claude-memory-compiler`, `gsd-build-get-shit-done` → `gsd`). For web sources, use the domain (strip `.com`/`.io`/etc when readable). **GitHub non-root pages treated as web sources are the exception:** derive the product slug from the repo portion of the page slug/source URL (for example `modelcontextprotocol-servers-tree-main-src-sequentialthinking` → `servers`). Sources describing the same product (e.g. a marketing site + its own GitHub repo) share the same `product:` slug. Resolved in Step 2b below.

`companion_urls:` and `raw_files:` are present **only** on unified web+github pages (when `companion_slug` is non-null). **Omit both fields entirely** on standalone web, github, and youtube source pages — do not write empty lists.

If the page **already exists** (this is an update or refresh): preserve the existing `created`, `tags`, `related`, `product`, `source_url`, `companion_urls`, and `raw_files` values. Always overwrite `updated` and `detail_level`.

**MUST NOT include a `sources:` field.** Source pages do not cite themselves.

**Body structure:**

1. Summary paragraph — what this source is and why it matters for the wiki's domain.
2. Banner citation: `_All claims below are sourced from ../../raw/<type>/<slug-file>.md unless otherwise noted._`
   - **Unified web+github exception:** the banner always cites the primary **web** raw file only. GitHub-sourced material is cited inline at the paragraph level.
3. Sectioned body by type:
   - **GitHub:** What it does | Installation | Key features | Architecture | Example usage | Maintenance status
   - **YouTube:** What the video is about (1 paragraph — sufficient to replace watching) | Key points by chapter | Notable quotes | Speaker context
   - **Web/product (no companion):** What it does | Key features | Architecture and concepts | Main APIs | When to use | Ecosystem
   - **Web/product (unified — `companion_slug` non-null):** see **Unified body structure** below

**Unified body structure** (web source with companion GitHub — `companion_slug` non-null):

```
<Summary paragraph — synthesized web + github perspective>

_All claims below are sourced from ../../raw/web/<domain>.md unless otherwise noted._

## What it does
<web-sourced; banner covers — no inline citation needed>

## Key features
<web-sourced for product features; github technical detail ends with: (../../raw/github/<org>-<repo>.md)>

## Architecture
<github-sourced; each paragraph ends with: (../../raw/github/<org>-<repo>.md)>

## Installation
<github-sourced; inline-cited: (../../raw/github/<org>-<repo>.md)>

## Example usage
<github-sourced; inline-cited: (../../raw/github/<org>-<repo>.md); this section is required even if it is only one short paragraph or command block>

## When to use
<web-sourced; banner covers>

## Maintenance status
<github-sourced — stars, release, license, roadmap; inline-cited: (../../raw/github/<org>-<repo>.md)>

## Ecosystem
<web-sourced; banner covers>

## Documentation   [optional — only if web raw has a substantial docs structure]
<web-sourced; banner covers>
```

The banner cites the primary web raw file. All github-sourced paragraphs carry trailing inline citations `(../../raw/github/<org>-<repo>.md)`. Both formats satisfy lint check #8 (citation path format — relative-from-file).

These headings are canonical for unified pages. Do not rename, skip, or replace them with ad hoc sections like "Agent integration". Fold that material into **Architecture**, **Example usage**, or **Ecosystem** instead.

**Formatting rules — apply uniformly to every source page:**

- **No H1 heading.** The page slug (filename) and the `[[<slug>]]` wikilink in `wiki/index.md` already serve as the title. Body starts with the summary paragraph; first heading in the body is the first `## H2` section.
- **No horizontal rules (`---`) between sections.** `## H2` headings provide enough structure. The only `---` lines are the YAML frontmatter delimiters.
- **Populate `tags` and `related` at ingest time.**
  - `tags`: 4–8 short kebab-case terms describing the source's main concepts, technologies, and domains. Specific over generic — prefer `claude-code-hooks`, `index-guided-retrieval`, `provider-adapter` over `ai`, `code`, `tool`. Pulled from the source's own headings, key features, and summary.
  - `related`: slugs of existing source pages (in `wiki/sources/`) with substantial conceptual overlap (same problem space, shared architecture pattern, same underlying tool, etc.). Read each existing source's summary paragraph to judge overlap. May be empty if this is the first source ingested or there is no real overlap. Casual mentions do not count as related.
  - **Bidirectional update:** for every slug `Y` that you add to this page's `related` list, also append this page's slug to `Y`'s `related` list (in `wiki/sources/Y.md`). Update `Y`'s `updated:` date. Without this, related references drift one-way — newly ingested pages link backward to older ones, but older pages never gain forward links to newer ones.
- **Use the per-type section list as the canonical structure.** Keep the listed sections, in the listed order. Extra top-level sections are allowed only for genuinely substantial subsystems that don't fit elsewhere; fold incidental content (config, workflow, etc.) into one of the standard sections instead.

Add per-paragraph inline citations only when a **second** raw file contributes to this page. The banner covers all content from the primary raw file alone.

---

## Step 2b — Detect product grouping

After writing the source page, scan existing source pages in `wiki/sources/` (excluding the page just written) and resolve a `product:` value:

- **GitHub source:** read `homepageUrl` from the raw file's `## Metadata` block. Extract its hostname (strip `www.`, preserve subdomains). If any existing **web** source page has a slug equal to that hostname, set `product:` on both pages to that hostname. Otherwise derive the product slug from the repo slug: strip the author prefix (e.g. `obra-superpowers` → `superpowers`, `coleam00-claude-memory-compiler` → `claude-memory-compiler`, `gsd-build-get-shit-done` → `gsd`). Use the derived slug.
- **Web source:** scan the raw file body for a `github.com/<org>/<repo>` URL appearing in the landing page's first ~500 chars or in the page title/hero. If `<org>-<repo>` matches an existing **github** source slug, set `product:` on both pages to the web source's slug (the domain or page slug). Otherwise derive the product slug from the domain (strip `.com`/`.io`/`.dev` suffix when the result is still recognizable, e.g. `runcabinet.com` → `cabinet`). **GitHub non-root web pages are the exception:** derive the product slug from the repo segment instead of `github.com` (for example `/modelcontextprotocol/servers/tree/main/src/sequentialthinking` → `servers`). Use the derived slug.
- **YouTube sources:** derive from the video title or channel name (short, kebab-case). Never auto-grouped with other sources.
- `product:` is always populated — never left as `null` after Step 2b.

If a grouping is applied, also update the partner page's `product:` field in place. Report the grouping in the post-ingest confirmation so the human can verify or override (humans may set `product:` manually for cases the heuristic misses).

## Step 3 — Do NOT create extra cross-source pages during ingest

`wiki/overview.md` is the only cross-source page. Ingest writes source pages plus `wiki/overview.md` only. Skip any additional cross-source page creation.

---

## Step 4 — Update `wiki/index.md`

1. Read `wiki/index.md`.
2. **If a row for this slug already exists** in the Sources table: update its date column and `detail_level` column in-place (do not add a new row; do not change the count).
3. **If no row exists:** add a row to the Sources table:
   `| [[<slug>]] | <type> | <effective_detail_level> | <today> | |`
   Then find the `_N sources ingested._` line and increment N by 1.
4. Write the updated file.

---

## Step 5 — Update `wiki/overview.md`

**Invariant:** the body of `wiki/overview.md` contains **exactly one paragraph per entry in `sources:`**, in the same order. Number of paragraphs must equal the length of the `sources:` list. Verify this before writing.

1. Read `wiki/overview.md`. Check the `sources:` frontmatter list and count the body paragraphs.

2. **If `"[[<slug>]]"` already appears in `sources:`** — this is a refresh:
   - Update the `updated:` frontmatter field to `<today>`. Do not add another paragraph or duplicate the frontmatter entry.
   - Write the updated file and stop at this step.

3. **If `sources:` is empty (`sources: []`)** — this is the first source ingested:
   - Replace the placeholder body (the `_No sources ingested yet..._` paragraph) with an opening overview paragraph describing what this source covers and what it contributes to understanding the domain. Cite `[[<slug>]]`.
   - Update `sources:` frontmatter to: `sources:\n  - "[[<slug>]]"`

4. **If `sources:` already has entries but does not include this slug** — extend the existing overview:
   - **Append a new dedicated paragraph for this source** at the end of the body. Do not merge the new source into an existing paragraph; do not skip writing one. The paragraph should summarize the source on its own terms and what it adds to the domain. Cite `[[<slug>]]` at least once.
   - **Do not reference other source pages by default.** Only mention another `[[source page]]` when there is substantial conceptual overlap, a direct product relationship, or a specific conflict/comparison that genuinely helps the reader.
   - Append `  - "[[<slug>]]"` to the `sources:` frontmatter list.

5. **Sanity check before writing:** the post-write paragraph count must equal `len(sources)`. If it doesn't, you've dropped or merged a paragraph — fix it.
6. Update the `updated:` frontmatter field to `<today>`.
7. Write the updated file.

---

## Step 6 — Append to `wiki/log.md`

Read `wiki/log.md`. Insert this block below the frontmatter block and the `# ... wiki — log` heading, **above** any existing `## ...` entries (newest at top):

```
## <today> | ingest | <slug> | <one-line summary from the raw file>

- Created: wiki/sources/<slug>.md
- Updated: wiki/index.md, wiki/overview.md, wiki/log.md, raw/<type>/README.md, inbox.md
```

When `companion_slug` is non-null, extend the Updated line and add a Companion line:
```
- Updated: wiki/index.md, wiki/overview.md, wiki/log.md, raw/web/README.md, raw/github/README.md, inbox.md
- Companion: raw/github/<companion_slug>.md
```

The `- Companion:` line is required on every unified web+github ingest entry.

Write the updated file.

---

## Step 7 — Update `raw/<type>/README.md`

Read `raw/<type>/README.md`.

**If a row for this slug already exists** in the Files table: update its `last-fetched` date column in-place (do not append a new row).

**If no row exists:** append one row to the Files table:
- **GitHub:** `| raw/github/<org>-<repo>.md | <org>/<repo> | <stars> | <default-branch> | <latest-release> | <today> | |`
- **YouTube:** `| raw/youtube/<video-id>-<slug>.md | <title> | <channel> | <duration> | <upload-date> | <today> | |`
- **Web:** `| raw/web/<slug>.md | <slug> | <pages-fetched> | <today> | |`

Write the updated file.

**When `companion_slug` is non-null:** also update `raw/github/README.md`. The companion row was already written during the companion fetch step in `add.md`/`run.md` — verify it exists and update the date in-place. Do not append a duplicate row.

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
