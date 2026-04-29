# run / add — process inbox or ingest a single URL

(Skill-directory paths and the `.pin-llm-wiki.yml` Guard are defined in `SKILL.md` — they apply here.)

## Invocation forms

```
/pin-llm-wiki run               ← batch: process every pending item
/pin-llm-wiki run <url>         ← single: process only this URL from Pending
/pin-llm-wiki add <url> [tags]  ← single: queue (if not already) then ingest atomically
```

`add` and `run <url>` produce identical filesystem state for the same URL. `add` is the convenience entry point — if the URL is missing from inbox it is queued automatically, then a single-URL ingest runs.

**Single-URL error cases** (stop immediately):
- URL found under `## Completed` (already ingested) → "URL already completed. To re-fetch, add `<!-- refresh -->` to its inbox line and run `/pin-llm-wiki run` again."
- URL found under `## Pending` with `<!-- skip -->` → "URL is marked `<!-- skip -->` — remove the tag from `inbox.md` to process it."
- (`run <url>` only) URL not found under `## Pending` → "URL not found in Pending: `<url>`. Add it with `/pin-llm-wiki queue <url>` first, or use `/pin-llm-wiki add <url>` to queue+ingest in one step."

---

## Setup

Read `.pin-llm-wiki.yml` and extract: `domain`, `detail_level`, `source_types`, `auto_mark_complete`, `auto_lint`.

Set `today` = current date in `YYYY-MM-DD` format.

Set `mode`:
- `add` invocation → `mode = "add"`
- `run <url>` invocation → `mode = "single"`
- `run` (no arg) invocation → `mode = "batch"`

Initialize a **run log** (empty list): `{pass, url, slug, outcome}` entries appended as each item completes.

---

## Pass 0 — Queue (mode = "add" only)

Skip in `single` and `batch` modes.

Read `inbox.md`. Locate the URL:
- **Already under `## Completed`:** stop with the "already completed" error above.
- **Already under `## Pending`:** use the existing line as-is — do not append a duplicate. Inline tags supplied with `add` are **ignored** in favor of the existing line's tags (the user can edit inbox.md to change tags).
- **Not in inbox.md:** append a new line to `## Pending`: `- [ ] <url> <any tags from invocation>`.

Re-read `inbox.md` after any mutation.

Then fall through to Pass 1 in single-URL mode (treat the queued URL as the single target).

---

## Pass 1 — Process pending items

Read `inbox.md`. Collect all lines matching `- [ ] ...` under `## Pending`, in order top-to-bottom.

**In `single` or `add` mode:** filter the collected lines to only the one whose URL matches the target. (Error cases above already fired before this point.)

For each such line:

### 1. Skip check

If the line contains `<!-- skip -->`: append `{pass: 1, url, outcome: skipped}` to the run log, leave the line as-is, continue to next.

### 2. Parse the line

Read `<skill-dir>/templates/protocols/common.md` § Inbox-line tag parsing. Extract URL, all tags, derive `effective_detail_level`, `companion_override_url`, `suppress_companion`.

### 3. Source type and slug

Read `<skill-dir>/templates/protocols/common.md` § Source-type detection and § Slug and raw-path derivation. Determine `type`, `slug`, `raw_file_path`.

### 4. Fetch

Read the protocol file for the detected type and follow it exactly:
- GitHub → `<skill-dir>/templates/protocols/github.md`
- YouTube → `<skill-dir>/templates/protocols/youtube.md`
- Web → `<skill-dir>/templates/protocols/web.md` (also handles GitHub non-root single-page mode)

Apply `<!-- branch:X -->` and `<!-- clone -->` (GitHub only). Use `effective_detail_level`.

**Fetch failure handling:**

| Failure | Action |
|---|---|
| YouTube, no transcript | Flag line with `<!-- fetch-failed:no-transcript -->`. Leave in `## Pending`. Log `fetch-failed:no-transcript`. Continue. |
| 200k token guard | Cumulative input tokens approach 200k → halt the entire run, surface to user. |
| Other error | Log error. Leave line in `## Pending`. Continue. |

### 5. Companion fetch (web sources only)

Read `<skill-dir>/templates/protocols/common.md` § Companion-fetch sub-protocol. The sub-protocol's gating conditions and self-loop guard apply.

### 6. Ingest

Read `<skill-dir>/ingest.md` and follow its instructions. Pass this context:

| Variable | Value |
|---|---|
| `slug` | derived above (YouTube: finalized after fetch step 1) |
| `type` | `github` / `youtube` / `web` |
| `raw_file_path` | derived above |
| `effective_detail_level` | override or config default |
| `auto_mark_complete` | from config |
| `today` | current date |
| `companion_slug` | from companion fetch (null if skipped/failed/multi-product) |
| `companion_raw_file_path` | from companion fetch (null otherwise) |
| `products` | list returned by web fetch step 5 (≥2 entries triggers multi-product ingest branch) |

Append `{pass: 1, url, slug, outcome: ingested}` to run log.

### 7. Re-read inbox before next item

`inbox.md` was mutated by ingest step 8. Re-read it before processing the next pending item.

---

## Pass 2 — Refresh tagged items

Skip in `add` mode (single-URL ingests don't trigger refresh sweeps).

Re-read `inbox.md`. Collect all lines under `## Completed` containing `<!-- refresh -->` (any `[ ]` / `[x]` state), in order. For each, run the **refresh flow**:

### 1. Resolve slug and raw path

Detect source type and derive slug/`raw_file_path` per common.md. For **YouTube**, the title is in the existing raw filename — scan `raw/youtube/` for files starting `<video-id>-`; if 0 or >1 matches, report and skip.

### 2. Read existing source page; determine shape

Read `wiki/sources/<slug>.md` frontmatter:

| Frontmatter signal | Shape |
|---|---|
| `raw_files:` present | **Unified web+github** |
| `subpages:` present | **Multi-product umbrella** |
| `parent_slug:` present | **Multi-product sub** — refresh **rejected**: "Cannot refresh sub-page directly. Add `<!-- refresh -->` to the umbrella's inbox line instead." |
| none of the above | **Standalone** |

Read existing raw file(s):
- **Unified:** every path in `raw_files:`.
- **Multi-product umbrella:** the single `raw_file_path` (shared with all subs).
- **Standalone:** `raw_file_path`.

Hold the before state in memory.

### 3. Re-fetch

**Unified:** for each path in `raw_files:`, choose the protocol from the prefix (`raw/web/` → web, `raw/github/` → github) and re-fetch. Hold new content without overwriting yet.

**Multi-product umbrella:** re-fetch via the web protocol at `effective_detail_level` (must be `deep`).

**Critical — do not shortcut discovery on refresh.** The natural temptation is to read the existing umbrella's `subpages:` list, conclude "those are the products," and re-fetch only those products' docs. **Do not.** It freezes the product set and defeats refresh. Required order:

1. Run web protocol structural fetches (steps 1–4) on the URL: curl llms.txt, fetch landing, fetch docs index. **Do not pre-load `subpages:`.** Fetch as if ingesting fresh.
2. Run web protocol step 5 (product discovery) **fully** including 5a (multi-depth candidates), 5b (product-node identification), 5c (classification), 5d (audit trail). The output is `discovered_products`.
3. Run step 6 (per-product docs fetch) on `discovered_products`, not on existing subs.
4. Continue through step 8 (write raw).

The existing `subpages:` list is consulted **only** in step 4 below, for the merge.

**Standalone:** re-fetch using the detected-type protocol.

**Refresh shape rules** (additive within shape only):
- Multi-product umbrella **gains** new sub-pages additively; never **loses** subs (use `remove <sub-slug>` manually).
- Standalone / unified pages are **not** auto-promoted to multi-product even if discovery returns ≥2 products. Log INFO suggesting `remove + re-add` if a promotion looks warranted.
- Unified pages do not gain or lose companions on refresh. `raw_files:`, `companion_urls:` preserved as-is.

### 4. Compare and write

Strip date-shaped frontmatter fields (matching `YYYY-MM-DD` or ISO 8601 timestamp) from both copies before comparing.

**Unified page:**
- `changed_raws` = files where new differs from old. `failed_fetches` = files that errored.
- All fetches failed → abort this item; log error; proceed to step 5.
- Some failed → log `WARN: partial refresh for <slug>`; proceed with `changed_raws` only.
- `changed_raws` non-empty → overwrite each changed raw; run ingest steps 2–5 and 7 (skip 6, 8, 9) with **unified context** (below).
- All unchanged → record `refresh: <slug> (no change)`.

**Unified-page ingest context for refresh:** locate the `../../raw/github/...md` entry in `raw_files:`; strip prefix and `.md` to get `companion_slug`, use the path (with leading `../../` dropped) as `companion_raw_file_path`. The primary `raw_file_path` is the `../../raw/web/...` entry, normalized. Pass these to ingest. Pass `products = []`.

**Multi-product umbrella:**
- Identical content → `refresh: <slug> (no change)`.
- Differs → overwrite `raw_file_path`, run ingest steps 2c, 4, 5, 7 (skip 6, 8, 9). Build the `products` list passed to ingest as the **union of existing subs and newly-discovered products**:
  1. **Existing entries** — for each `<sub-slug>` in the umbrella's `subpages:`, read `wiki/sources/<sub-slug>.md` and extract `product:` (slug) and `source_url:` (`deep_link_url`). Resolve display `name` by matching the product slug against the new raw's `## Product: <Name>` headings; fall back to the sub-page's first body heading or a title-cased slug.
  2. **New entries** — parse the new raw for every `## Product: <Name>` section. For each whose slug is not already in step 1's list, append as a new `products` entry. New sub-slug = `<umbrella>-<product>`. Log INFO: `refresh: <umbrella> | new sub-page: <new-sub-slug>`.
  3. **Stale entries** — entries from step 1 whose product slug is missing in the new raw are kept in `products` (so the sub is preserved). Log INFO: `refresh: <umbrella> | sub-page <sub-slug> retained — product not in new discovery; remove manually if upstream dropped it`. Step 2c.3 detects stale entries (no matching `## Product:` section) and skips body regeneration for them, only updating `updated:`.
  
  Pass merged `products` to ingest with `companion_slug = null`. Step 2c writes/updates umbrella body (with the updated `subpages:` list) and each sub-page body.

**Standalone:**
- Identical → `refresh: <slug> (no change)`.
- Differs → overwrite `raw_file_path`; run ingest steps 2–5 and 7. Pass `companion_slug = null`, `companion_raw_file_path = null`, `products = []`.

If content changed, append to `wiki/log.md` (newest at top):
```
## <today> | refresh | <slug> | content updated

- Updated: wiki/sources/<slug>.md, wiki/index.md, wiki/overview.md, wiki/log.md
- Raw: <comma-separated changed raw paths>
```

### 5. Update inbox line

- Remove `<!-- refresh -->`; append `<!-- refreshed <today> -->`. Preserve `[ ]` / `[x]` state.
- Write `inbox.md`.

Append `{pass: 2, url, slug, outcome: refreshed | no-change}` to run log.

---

## Post-run lint

- `auto_lint: batch` → read `<skill-dir>/lint.md` and run the full lint. Include report in summary below.
- `auto_lint: never` or `per-ingest` → skip lint here. (Per-ingest lint is suppressed inside `run` — it never fires per-item; it fires once at the end via `batch`, or not at all.)

In `add` mode, `auto_lint: per-ingest` **does** trigger lint after the single ingest (the per-ingest semantics still apply for the convenience entry point).

---

## Summary report

### `batch` mode

```
run complete — <domain> wiki
<today>

Pass 1 — pending:
  Ingested: N
  Skipped:  N  (<!-- skip --> tag)
  Failed:   N  (fetch errors logged above)

Pass 2 — refresh:
  Updated:   N
  No change: N

[Lint: <N ERROR, N WARN, N INFO — see report above>]
[Lint: skipped (auto_lint: <never|per-ingest>)]
```

### `single` or `add` mode

```
Ingested: <url>

  Type:        <github | youtube | web>
  Slug:        <slug>
  Raw:         <raw_file_path>
  Wiki page:   wiki/sources/<slug>.md
  Detail:      <effective_detail_level>
  Companion:   raw/github/<org>-<repo>.md   ← only when companion fetch succeeded
  Products:    <product1>, <product2>, ...  ← only in multi-product mode
  Sub-pages:   wiki/sources/<slug>-<product1>.md, ...

Updated: wiki/index.md, wiki/overview.md, wiki/log.md, raw/<type>/README.md, inbox.md
```

If the companion fetch was attempted but failed: `  Companion:   fetch failed (<reason>) — web-only page produced`.
If the detected type is not in `source_types`, append: `  Note: source type <type> is not in this wiki's source_types config.`

Suggested commit message for the human (do not commit yourself): `ingest: <slug>` or `refresh: <slug>`.

---

## Notes

- **Idempotency:** items remain under `## Pending` until successfully ingested. A crashed run can be safely re-run.
- **`<!-- skip -->` is persistent:** remove the tag manually to process the item.
- **Partial raw on crash:** the partial raw file (if any) will be overwritten on re-fetch — no manual cleanup needed.
- **No agent commits** — see SKILL.md Git policy.
