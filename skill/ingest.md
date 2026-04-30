# ingest — shared ingest protocol

Called by `add`, `run`, and `refresh`. Execute steps in order.

**Context passed in by the caller:**

| Variable | Value |
|---|---|
| `slug` | source identifier (e.g. `langchain-ai-langchain`, `abc123-video-title`, `docs.langchain.com`, `modelcontextprotocol-servers-tree-main-src-sequentialthinking`). For multi-product mode, this is the **umbrella slug** (e.g. `langchain.com`). |
| `type` | `github` / `youtube` / `web` |
| `raw_file_path` | path to the completed raw file (e.g. `raw/github/langchain-ai-langchain.md`, `raw/web/modelcontextprotocol-servers-tree-main-src-sequentialthinking.md`) |
| `effective_detail_level` | resolved detail level (`brief` / `standard` / `deep`) |
| `auto_mark_complete` | from `.pin-llm-wiki.yml` |
| `today` | current date `YYYY-MM-DD` |
| `companion_slug` | `<org>-<repo>` if a companion GitHub repo was fetched; `null` otherwise. **Always null in deep multi-product mode.** |
| `companion_raw_file_path` | `raw/github/<org>-<repo>.md` if companion fetch succeeded; `null` otherwise |
| `products` | list of `{name, slug, deep_link_url?, docs_url?, repo_url?}` returned by web fetch step 5; `[]` for single-product, `null` for non-web. Drives the multi-product branch in Step 2. |

---

## Step 1 — Read the raw file(s)

Read `raw_file_path` fully before writing any wiki content.

If `companion_raw_file_path` is non-null: also read it fully. Hold both in memory. The companion raw file supplies content for the github-sourced sections of the unified source page.

In **deep multi-product mode** (`products` has ≥2 entries), the raw file's `## Fetch log` should include `Mode: deep-multi-product` and a `## Product: <Name>` section per product. Confirm this matches `products` before continuing — if the raw file does not contain matching sections, abort and ask the human to re-fetch (the caller passed mismatched context).

---

## Step 2 — Branch on shape

Three ingest shapes are possible. Pick the one that fits this ingest:

| Shape | Trigger | Output |
|---|---|---|
| **Standalone** | `type` is github/youtube/web, `companion_slug` is null, `products` is empty/null | one source page at `wiki/sources/<slug>.md` |
| **Unified web+github** | `type=web`, `companion_slug` non-null, `products` empty/null | one source page at `wiki/sources/<slug>.md` with `companion_urls:` and `raw_files:` frontmatter |
| **Multi-product (deep web)** | `type=web`, `effective_detail_level=deep`, `products` has ≥2 entries | umbrella page at `wiki/sources/<slug>.md` + one sub-page per product at `wiki/sources/<slug>-<product-slug>.md` |

**Standalone and Unified flows:** continue with Step 2a (single source page). This is the existing behavior, unchanged.

**Multi-product flow:** continue with Step 2c (umbrella + sub-pages). Skip Step 2a.

---

## Step 2a — Create or update `wiki/sources/<slug>.md` (standalone / unified)

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

After Step 2a, continue with Step 2b (product grouping), then Step 4 onward.

---

## Step 2b — Detect product grouping (standalone / unified only)

Runs only after Step 2a (the multi-product Step 2c assigns `product:` explicitly and skips this step).

After writing the source page, scan existing source pages in `wiki/sources/` (excluding the page just written) and resolve a `product:` value:

- **GitHub source:** read `homepageUrl` from the raw file's `## Metadata` block. Extract its hostname (strip `www.`, preserve subdomains). If any existing **web** source page has a slug equal to that hostname, set `product:` on both pages to that hostname. Otherwise derive the product slug from the repo slug: strip the author prefix (e.g. `obra-superpowers` → `superpowers`, `coleam00-claude-memory-compiler` → `claude-memory-compiler`, `gsd-build-get-shit-done` → `gsd`). Use the derived slug.
- **Web source:** scan the raw file body for a `github.com/<org>/<repo>` URL appearing in the landing page's first ~500 chars or in the page title/hero. If `<org>-<repo>` matches an existing **github** source slug, set `product:` on both pages to the web source's slug (the domain or page slug). Otherwise derive the product slug from the domain (strip `.com`/`.io`/`.dev` suffix when the result is still recognizable, e.g. `runcabinet.com` → `cabinet`). **GitHub non-root web pages are the exception:** derive the product slug from the repo segment instead of `github.com` (for example `/modelcontextprotocol/servers/tree/main/src/sequentialthinking` → `servers`). Use the derived slug.
- **YouTube sources:** derive from the video title or channel name (short, kebab-case). Never auto-grouped with other sources.
- `product:` is always populated — never left as `null` after Step 2b.

If a grouping is applied, also update the partner page's `product:` field in place. Report the grouping in the post-ingest confirmation so the human can verify or override (humans may set `product:` manually for cases the heuristic misses).

After Step 2b, continue with Step 4.

---

## Step 2c — Multi-product: write umbrella + sub-pages

Run this step **instead of** Step 2a (and Step 2b) when `products` has ≥2 entries. Step 2b is skipped — the per-page `product:` assignments below are explicit.

### 2c.1 — Resolve sub-slugs

For each entry `p` in `products`:
- `sub_slug = "<slug>-<p.slug>"` — e.g. `langchain.com-langgraph`. The umbrella slug is `<slug>`.
- `sub_source_url = p.deep_link_url if non-null else <original URL>` — prefer the product-specific page on the source site for provenance; fall back to the parent URL.

### 2c.2 — Write the umbrella page `wiki/sources/<slug>.md`

**Frontmatter:**

```yaml
---
type: source
source_url: <original URL of the source>
subpages:
  - <slug>-<product1-slug>
  - <slug>-<product2-slug>
  - ...
tags: []
related: []
product: <slug>                # the umbrella's product slug is the umbrella slug itself (the domain) — distinct from any sub
detail_level: deep
created: <today>
updated: <today>
---
```

- `subpages:` is a list of plain sub-slugs (no wikilink syntax, no leading `wiki/sources/`). Required on every umbrella page; absent on every other page.
- `product:` on the umbrella is the umbrella slug itself (e.g. `langchain.com`). This guarantees no collision with sub `product:` values, so lint check #11 (split-product) does not fire for the umbrella + its subs.
- **Omit** `companion_urls:` and `raw_files:` — multi-product umbrellas do not have a github companion. Each sub may carry a `repo_url` in the raw file; the human can ingest those separately as needed.
- **MUST NOT include** `sources:` or `parent_slug:`.

If the umbrella **already exists** (refresh): preserve `created`, `tags`, `related`, `product`, `source_url`. Always overwrite `updated` and `detail_level`. The `subpages:` list is rewritten from the merged `products` list passed by the caller — this is how refresh can add new sub-pages when discovery turns up a product the original ingest missed (run.md, Step 4 of the refresh flow handles the merge: existing subs + new products = additive). Never **drop** an existing sub-slug from `subpages:` during refresh — refresh keeps stale entries; only `remove` deletes a sub.

**Body structure:**

```
<Summary paragraph — what platform this is, what it offers, who it's for>

_All claims below are sourced from ../../raw/web/<slug>.md unless otherwise noted._

## Products
- [[<slug>-<product1-slug>]] — <one-sentence what-it-is>
- [[<slug>-<product2-slug>]] — <one-sentence what-it-is>
- ...

## Architecture
<Optional — how the products fit together (open-source frameworks, hosted offering, monetization model). Banner covers.>

## When to use the platform
<Operator-facing summary of the situations where this platform makes sense as a whole. Banner covers.>

## Documentation
<Brief description of the docs structure — the docs site URL and how product subsections are organized. Banner covers.>
```

The umbrella is a **hub page**, not a deep dive. Detail lives in each sub-page. Avoid repeating product-specific feature lists on the umbrella — link to the sub.

### 2c.3 — Write each sub-page `wiki/sources/<slug>-<product-slug>.md`

For each entry `p` in `products`:

**Frontmatter:**

```yaml
---
type: source
source_url: <p.deep_link_url or umbrella source_url>
parent_slug: <slug>
tags: []
related: []
product: <p.slug>              # e.g. langgraph
detail_level: deep
created: <today>
updated: <today>
---
```

- `parent_slug:` is the umbrella slug (no wikilink syntax). Required on every sub-page; absent on every other page.
- `product:` is the product's own slug (e.g. `langgraph`), distinct from the umbrella's `product:`.
- **Omit** `companion_urls:`, `raw_files:`, `subpages:`, `sources:`.

If the sub-page **already exists** (refresh): preserve `created`, `tags`, `related`, `product`, `source_url`, `parent_slug`. Always overwrite `updated` and `detail_level`.

**Body structure** — standard web/product (no companion):

```
<Summary paragraph — what this product is, where it sits in the platform, why it matters>

_All claims below are sourced from ../../raw/web/<slug>.md unless otherwise noted._

## What it does
<from this product's docs and product page in the raw file>

## Key features
<from the product's docs and feature highlights>

## Architecture and concepts
<from the product's docs — core concepts, building blocks>

## Main APIs
<from the product's docs — entry points, primary functions/classes if applicable>

## When to use
<operator-facing — when does this product fit?>

## Ecosystem
<related components within or outside the platform; if the product has a separate GitHub repo, mention it here>
```

The banner cites the **same** raw file as the umbrella (`../../raw/web/<slug>.md`). Every sub-page shares one raw file with the umbrella — that is the explicit design constraint of multi-product deep mode: one ingest, one raw file, many wiki pages.

If the raw file's `## Product: <Name>` section is sparse (the product was discovered via repo URL only, no `docs_url`), the sub-page may be short; note in the summary paragraph that fuller detail will require a separate ingest of the product's repo.

**Refresh: stale-entry handling.** During refresh, the `products` list passed by the caller may include "stale" entries — sub-pages whose product slug does not match any `## Product:` section in the new raw file (the run.md refresh flow keeps them rather than dropping). For these entries, **do not regenerate the body** (there is no source material in the new raw to regenerate from). Skip body rewrite entirely; only update the sub-page's `updated:` frontmatter to `<today>`. The existing body is preserved verbatim. Detect a stale entry by attempting to locate `## Product: <Name>` (or matching by product slug against each section's `- Slug:` line) — if no match, mark the entry stale.

### 2c.4 — Tags and related across umbrella + subs

- The umbrella's `tags:` describe the platform as a whole (3–6 short kebab-case terms).
- Each sub's `tags:` describe that product specifically. Do not duplicate the umbrella's tags verbatim — pick what is product-specific.
- `related:`: each sub may list its sibling subs only when there is genuine functional dependency or cross-use that benefits the reader. Default is empty between siblings — the umbrella already wikilinks each sub from `## Products`, which covers basic discoverability.
- The bidirectional `related` rule applies as usual when adding cross-source `related` entries to sources outside this product family.

After Step 2c, continue with Step 4 (Step 2b is not run in this branch).

---

## Step 3 — Do NOT create extra cross-source pages during ingest

`wiki/overview.md` is the only cross-source page. Ingest writes source pages plus `wiki/overview.md` only.

In multi-product flow, the umbrella and its subs are all source pages; they are not cross-source synthesis pages, even though they were produced by one ingest. Do not produce additional pages beyond the umbrella + subs + overview.

---

## Step 4 — Update `wiki/index.md`

1. Read `wiki/index.md`.
2. **Standalone / unified:** for the single source page being written, update its row in the Sources table in-place if it exists, or add a new row and increment `_N sources ingested._`.
3. **Multi-product:** add a row for the **umbrella** AND a row for **each sub-page** (or update each in-place if it already exists). Each row uses the same `<type>` (`web`) and `<effective_detail_level>` (`deep`) and today's date. Increment `_N sources ingested._` by the number of NEW rows added (umbrella + subs that did not previously exist). On refresh, the count is unchanged.

Row format (same for all): `| [[<slug>]] | <type> | <effective_detail_level> | <today> | |`

4. Write the updated file.

---

## Step 5 — Update `wiki/overview.md`

**Invariant:** the body of `wiki/overview.md` contains **exactly one paragraph per entry in `sources:`**, in the same order. Number of paragraphs must equal the length of the `sources:` list. Verify this before writing.

1. Read `wiki/overview.md`. Check the `sources:` frontmatter list and count the body paragraphs.

2. **Standalone / unified flow:** treat the single source page as the only new entry. Apply the rules below for that one slug.

3. **Multi-product flow:** treat the **umbrella** AND **each sub-page** as separate new entries. Each gets its own `sources:` entry and its own dedicated paragraph. Add the umbrella first, then the subs in the order they appear in `products`.

**Per-entry rules** (apply for each new slug, in order):

- **If `"[[<slug>]]"` already appears in `sources:`** — this is a refresh:
  - Update the `updated:` frontmatter field to `<today>`. Do not add another paragraph or duplicate the frontmatter entry.

- **If `sources:` is empty (`sources: []`) and this is the first entry overall:**
  - Replace the placeholder body with an opening overview paragraph describing what this source covers and what it contributes to understanding the domain. Cite `[[<slug>]]`.
  - Update `sources:` frontmatter to: `sources:\n  - "[[<slug>]]"`

- **If `sources:` already has entries but does not include this slug:**
  - **Append a new dedicated paragraph for this source** at the end of the body. Do not merge into an existing paragraph. The paragraph should summarize the source on its own terms and what it adds to the domain. Cite `[[<slug>]]` at least once.
  - For multi-product, the umbrella's paragraph may wikilink each sub via `[[<slug>-<product>]]`; sub-page paragraphs should focus on what the product specifically adds, with a short link back to `[[<umbrella-slug>]]` for context.
  - **Do not reference unrelated source pages by default.** Only mention another `[[source page]]` when there is substantial conceptual overlap, a direct product relationship, or a specific conflict/comparison that genuinely helps the reader.
  - Append `  - "[[<slug>]]"` to the `sources:` frontmatter list.

4. **Sanity check before writing:** the post-write paragraph count must equal `len(sources)`. If it doesn't, fix it.
5. Update the `updated:` frontmatter field to `<today>`.
6. Write the updated file.

---

## Step 6 — Append to `wiki/log.md`

Read `wiki/log.md`. Insert this block below the frontmatter block and the `# ... wiki — log` heading, **above** any existing `## ...` entries (newest at top).

**Standalone / unified:**

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

**Multi-product:** one log entry covers the whole ingest:

```
## <today> | ingest | <slug> | multi-product (<N> products): <comma-separated product names>

- Created: wiki/sources/<slug>.md, wiki/sources/<slug>-<product1>.md, wiki/sources/<slug>-<product2>.md, ...
- Updated: wiki/index.md, wiki/overview.md, wiki/log.md, raw/web/README.md, inbox.md
```

The `Created:` line lists the umbrella plus every sub-page that was newly created in this ingest. On refresh, replace `Created:` with `Updated:` for any pages that already existed.

Write the updated file.

---

## Step 7 — Update `raw/<type>/README.md`

Read `raw/<type>/README.md`.

**If a row for this slug already exists** in the Files table: update its `last-fetched` date column in-place (do not append a new row).

**If no row exists:** append one row to the Files table:
- **GitHub:** `| raw/github/<org>-<repo>.md | <org>/<repo> | <stars> | <default-branch> | <latest-release> | <today> | |`
- **YouTube:** `| raw/youtube/<video-id>-<slug>.md | <title> | <channel> | <duration> | <upload-date> | <today> | |`
- **Web:** `| raw/web/<slug>.md | <slug> | <pages-fetched> | <today> | |`

In multi-product mode there is still **one** raw web file (the umbrella's), so still one row.

Write the updated file.

**When `companion_slug` is non-null:** also update `raw/github/README.md`. The companion row was already written during the companion fetch step in `run.md` — verify it exists and update the date in-place. Do not append a duplicate row.

---

## Step 8 — Move inbox line

1. Read `inbox.md`.
2. Locate the URL's line under `## Pending`.
3. Append `<!-- ingested <today> -->` to the line.
4. If `auto_mark_complete: true`: flip `[ ]` → `[x]`.
5. Move the line (with the appended comment, updated checkbox) from `## Pending` to the bottom of `## Completed`.
6. Write the updated `inbox.md`.

In multi-product mode there is still **one** inbox line (the umbrella's URL); subs are wiki-only artifacts and do not get their own inbox lines.

---

## Step 9 — Git

No agent commits — see SKILL.md Git policy.
