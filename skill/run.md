# run — batch process pending inbox

> **Skill directory note:** This file is in the skill directory (e.g. `<skill-dir>/`, `~/.claude/skills/pin-llm-wiki/`, `~/.copilot/skills/pin-llm-wiki/`, or `~/.cursor/skills/pin-llm-wiki/`). All `templates/` and sibling-file paths below are relative to that same directory. Use whichever path applies to the tool that loaded this skill.

## Invocation forms

```
/pin-llm-wiki run              ← batch: process all pending items
/pin-llm-wiki run <url>        ← single: process only this URL from Pending
```

When a `<url>` argument is supplied, `run` operates in **single-URL mode**: only the inbox line whose URL exactly matches `<url>` is processed. Pass 1 processes only that one line; Pass 2 (refresh) runs normally (all `<!-- refresh -->` lines in Completed). All other behavior — fetch, ingest, lint, summary report — is identical.

**Single-URL error cases** (stop immediately, do not proceed):
- URL not found under `## Pending` → "URL not found in Pending: `<url>`. Add it with `/pin-llm-wiki queue <url>` first."
- URL found under `## Pending` but has `<!-- skip -->` tag → "URL is marked `<!-- skip -->` — remove the tag from `inbox.md` to process it."
- URL found under `## Completed` (already ingested) → "URL already completed. To re-fetch, add `<!-- refresh -->` to its inbox line and run `/pin-llm-wiki run` again."

---

## Guard

Check whether `.pin-llm-wiki.yml` exists in the current working directory. If not, stop:
> "No wiki found here (`.pin-llm-wiki.yml` missing). Run `/pin-llm-wiki init` to scaffold one first."

---

## Setup

Read `.pin-llm-wiki.yml` and extract: `domain`, `detail_level`, `source_types`, `auto_mark_complete`, `auto_lint`.

Set `today` = current date in `YYYY-MM-DD` format.

Initialize a **run log** (empty list): `{pass, url, slug, outcome}` entries appended as each item completes.

---

## Pass 1 — Process pending items

Read `inbox.md`. Collect all lines matching `- [ ] ...` under `## Pending`, in order top-to-bottom.

**In single-URL mode:** filter the collected lines to only the one line whose URL matches the `<url>` argument. If after filtering the list is empty, the error-case checks above already fired — this point is not reached.

For each such line:

### 1. Skip check

If the line contains `<!-- skip -->`: append `{pass: 1, url: <url>, outcome: skipped}` to the run log, leave the line as-is, continue to next.

### 2. Parse the line

Extract:
- **URL** — first token after `- [ ] `
- **Tags** — `<!-- detail:X -->`, `<!-- branch:X -->`, `<!-- clone -->` if present
- **Companion tags** (web only) — `<!-- companion:github.com/<org>/<repo> -->` → `companion_override_url`; `<!-- no-companion -->` → `suppress_companion = true`

### 3. Effective detail level

`<!-- detail:X -->` override if present; else `detail_level` from config.

### 4. Source type detection

| Pattern | Type |
|---|---|
| `github.com/<org>/<repo>` — exactly two non-empty path segments | `github` |
| `github.com/<org>/<repo>/<...>` — any additional path segments (for example `/tree/...`, `/blob/...`, `/issues/...`) | `web` |
| `youtube.com/watch?v=` or `youtu.be/<id>` | `youtube` |
| anything else | `web` |

### 5. Slug and raw path derivation

Same rules as `add`:

- **GitHub:** slug = `<org>-<repo>`, raw path = `raw/github/<org>-<repo>.md`
- **YouTube:** video ID from URL; title slug finalized after fetch step 1 (requires `yt-dlp --dump-json` output); full slug = `<video-id>-<title-slug>`; raw path = `raw/youtube/<video-id>-<title-slug>.md`
- **Web:** slug = hostname with `www.` stripped (preserve subdomains); raw path = `raw/web/<slug>.md`. Always one file per ingest, regardless of detail level. In deep multi-product mode the single raw file contains `## Product:` sections; ingest uses them to write one umbrella page plus one sub-page per product (sub-slug = `<slug>-<product-slug>`).
- **GitHub non-root page special case:** if the URL is `github.com/<org>/<repo>/<...>`, derive the web slug as `<org>-<repo>-<path-slug>`, where `<path-slug>` is the remaining path joined with hyphens and normalized to kebab-case. Example: `https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking` → `modelcontextprotocol-servers-tree-main-src-sequentialthinking`

### 6. Fetch

Read the protocol file for the detected type and follow it exactly:
- GitHub → `<skill-dir>/templates/protocols/github.md`
- YouTube → `<skill-dir>/templates/protocols/youtube.md`
- Web → `<skill-dir>/templates/protocols/web.md`

Apply `<!-- branch:X -->` and `<!-- clone -->` tags (GitHub only). Use the effective detail level.

**GitHub non-root page special case:** when the detected type is `web` because the URL is `github.com/<org>/<repo>/<...>`, treat it as a **single-page web capture**. Fetch only the exact URL. Skip `llms.txt`, docs discovery, and companion GitHub discovery regardless of detail level.

**Fetch failure handling:**

| Failure | Action |
|---|---|
| YouTube, no transcript | Flag line with `<!-- fetch-failed:no-transcript -->`. Leave in `## Pending`. Append `{pass: 1, url, outcome: fetch-failed:no-transcript}` to run log. Continue to next item. |
| 200k token guard | Cumulative input tokens for this source approaches 200k → halt the entire run, surface to user. Do not continue to remaining items. |
| Other error | Log the error. Leave line in `## Pending` unchanged. Append `{pass: 1, url, outcome: fetch-error: <reason>}` to run log. Continue to next item. |

### 6b. Companion fetch (web sources only)

**Only runs when:** type = web AND `companion_github_url` (returned by the web fetch protocol step 7) is non-null AND `suppress_companion` is false AND `products` (from web fetch step 5) is empty or has fewer than 2 entries. In deep multi-product mode the protocol returns `companion_github_url = null`, so this step is a no-op.

If `companion_override_url` is set, use it as `companion_github_url` instead of the discovered value.

**Self-loop guard:** if `companion_github_url` resolves to the same repo as the inbox URL, discard it and set `companion_github_url = null`.

Steps:
1. Derive `companion_slug` = `<org>-<repo>` and `companion_raw_file_path` = `raw/github/<org>-<repo>.md`.
2. Read `<skill-dir>/templates/protocols/github.md` and fetch `github.com/<org>/<repo>` using `effective_detail_level`. Inherit any `<!-- branch:X -->` tag.
3. Write `companion_raw_file_path`.
4. Update `raw/github/README.md` (add row or update in-place).

**Failure:** if fetch errors, append `{pass: 1, url, outcome: companion-fetch-warn: <reason>}` to run log, set `companion_slug = null`, continue with web-only ingest. Do not mark the item as failed — the primary fetch succeeded.

---

### 7. Ingest

Read `<skill-dir>/ingest.md` and follow its instructions.

Pass this context:

| Variable | Value |
|---|---|
| `slug` | derived above (YouTube: finalized after fetch step 1) |
| `type` | `github` / `youtube` / `web` |
| `raw_file_path` | derived above |
| `effective_detail_level` | override or config default |
| `auto_mark_complete` | from config |
| `today` | current date |
| `companion_slug` | `<org>-<repo>` if companion fetch succeeded; null otherwise (always null in deep multi-product mode) |
| `companion_raw_file_path` | `raw/github/<org>-<repo>.md` if companion fetch succeeded; null otherwise |
| `products` | list returned by web fetch step 5 (web sources only). Empty/null when only one product was discovered or detection is not applicable. ≥2 entries triggers the multi-product ingest branch. |

Ingest step 9 is a no-op for git—do not run `git commit` for ingest (see the wiki’s `AGENTS.md` **Git — never auto-commit**).

Append `{pass: 1, url, slug, outcome: ingested}` to run log.

### 8. Re-read inbox before next item

`inbox.md` was mutated by ingest step 8. Re-read it before processing the next pending item to pick up the updated state.

---

## Pass 2 — Refresh tagged items

Re-read `inbox.md`. Collect all lines under `## Completed` that contain `<!-- refresh -->` (regardless of `[ ]` / `[x]` state), in order.

For each such line, run the **refresh flow**:

### 1. Resolve slug and raw path

Extract URL and any type-detection tags. Detect source type (same rules as Pass 1). Derive slug and `raw_file_path` (same rules as Pass 1).

For **YouTube**: the full slug includes the title, which is encoded in the raw filename. Scan `raw/youtube/` for files whose name starts with `<video-id>-`. If exactly one match: use its full name as the slug. If zero matches: report error ("raw file for <video-id> not found — was this source ever ingested?") and skip. If more than one match: report error ("ambiguous raw files for <video-id>: <list>") and skip.

### 2. Read existing raw file(s)

Read the existing `wiki/sources/<slug>.md` frontmatter. Determine the page shape:

| Frontmatter signal | Shape |
|---|---|
| `raw_files:` present | **Unified web+github** |
| `subpages:` present | **Multi-product umbrella** |
| `parent_slug:` present | **Multi-product sub** — refresh **must** target the umbrella URL, not the sub. Stop with: "Cannot refresh sub-page directly. Add `<!-- refresh -->` to the umbrella's inbox line (`<umbrella-source-url>`) instead — the multi-product flow re-ingests the umbrella + all subs from one raw file." |
| none of the above | **Standalone** |

**Unified page** (`raw_files:` present): iterate over every path in `raw_files:`. For each, read the existing file (before state) and hold in memory.

**Multi-product umbrella** (`subpages:` present): the page shares **one** raw file with all its subs. Read `raw_file_path` (the single web raw) only.

**Standalone page**: read `raw_file_path` only.

### 3. Re-fetch

**Unified page:** for each raw file in `raw_files:`, determine the protocol from the path prefix (`raw/web/` → web protocol, `raw/github/` → github protocol) and re-fetch. Hold new content in memory without overwriting yet.

**Multi-product umbrella:** re-fetch using the web protocol at the same `effective_detail_level` (which must be `deep` since the page is multi-product).

**Critical — do not shortcut discovery on refresh.** The natural temptation is to read the existing umbrella's `subpages:` list, conclude "those are the products," and re-fetch only those products' docs pages. **Do not do this.** It freezes the product set at its current state and defeats the whole purpose of refresh — refresh exists precisely so newly-added upstream products can be picked up. Instead:

1. Run the web protocol's structural fetches (steps 1–4) on the URL: curl llms.txt, fetch the landing page, fetch the docs index. **Do not pre-load the existing `subpages:` list to inform what to fetch.** These structural fetches must run as if you were ingesting fresh.
2. Run web protocol step 5 (product discovery) **fully**, including step 5a (multi-depth candidate enumeration), step 5b (product-node identification), step 5c (classification), and step 5d (audit trail). Do not skip the sanity check. Do not derive the product list from the existing `subpages:`. The output of step 5 is `discovered_products`.
3. Run web protocol step 6 (per-product docs fetch) on **`discovered_products`**, not on the existing subs. If discovery found a product the existing wiki doesn't have, this is the only path that fetches its docs.
4. Continue the protocol through step 8 (write raw).

The existing `subpages:` list is consulted **only** in step 4 of this refresh flow (below) to merge the freshly discovered set with the existing subs. It plays no role in the fetch.

The protocol re-runs product discovery and per-product docs fetch. **Discovery output is additive on refresh:**
- Newly-discovered products that are not already represented in the umbrella's `subpages:` list become **new sub-pages** in step 4 (this is what makes refresh useful when the upstream gains a product or when the original ingest missed one).
- Existing sub-pages whose products no longer appear in the new discovery output are **kept** (refresh never deletes pages). They are flagged as INFO so the human can `remove <sub-slug>` if the upstream really removed the product.

Hold the new raw content and the new `products` list in memory without overwriting yet.

**Standalone page:** re-fetch using the detected-type protocol as before.

**Refresh shape rules.** Refresh is additive within a shape, not across shapes:
- A **multi-product umbrella** can gain new sub-pages on refresh (additive). Existing subs are never dropped.
- A **standalone** or **unified** page is **not** auto-promoted to multi-product even if the new discovery returns ≥2 products — the shape change is too invasive to do silently. Log an INFO suggesting `remove + re-add` if a promotion looks warranted.
- A **unified web+github** page does not gain or lose its companion on refresh. To change companion behavior, `remove + re-add`.
- A **multi-product umbrella** is never demoted to standalone, even if discovery now returns 0 or 1 products. Existing subs persist.

### 4. Compare

Strip from both copies any frontmatter field whose value matches `YYYY-MM-DD` or an ISO 8601 timestamp. Compare.

**Unified page:**
- `changed_raws` = list of raw files where new content differs from old.
- `failed_fetches` = list of raw files where re-fetch errored.
- All fetches failed → abort this item; append error to run log; proceed to step 5 (update inbox line).
- Some fetches failed → log `WARN: partial refresh for <slug> (<failed count> raw(s) failed: <paths>)`; proceed with `changed_raws` only.
- `changed_raws` non-empty → overwrite each changed raw; run ingest steps 2–5 and 7 (skip 6, 8, 9) **with unified context** (see below); write refresh log entry below.
- All unchanged → record `refresh: <slug> (no change)`.

**Unified-page ingest context for refresh:** derive companion context from the existing source page's `raw_files:` list — locate the entry beginning with `../../raw/github/`, strip the prefix and `.md` suffix to get `companion_slug`, and use the path as `companion_raw_file_path`. The primary `raw_file_path` is the `../../raw/web/...` entry from the same list, normalized to `raw/web/<slug>.md` (the leading `../../` is dropped since ingest paths are repo-relative). Pass `companion_slug` and `companion_raw_file_path` to ingest so it preserves the unified body and frontmatter. Pass `products = []`.

**Multi-product umbrella:**
- If content is identical → record `refresh: <slug> (no change)`.
- If content differs → overwrite `raw_file_path`, run ingest steps 2c, 4, 5, and 7 (skip 6, 8, 9). Build the `products` list passed to ingest as the **union of existing subs and newly-discovered products**:
  1. **Existing entries** — for each `<sub-slug>` in the umbrella's `subpages:` list, read `wiki/sources/<sub-slug>.md` and extract `product:` (the product slug) and `source_url:` (the `deep_link_url`). Resolve the display `name` by matching the product slug against the new raw file's `## Product: <Name>` headings (the heading text after `## Product: ` is the display name); if no match, fall back to the sub-page's first body heading or, last resort, a title-cased slug.
  2. **New entries** — parse the new raw file for every `## Product: <Name>` section. For each, read its `- Slug:`, `- Deep link:`, `- Docs URL:`, and `- Companion repo:` lines. If the slug is **not** already represented in step 1's existing entries, append it to `products` as a new entry — this becomes a new sub-page. The new sub-slug is `<umbrella-slug>-<product-slug>` (Step 2c.1 derivation). Log INFO: `refresh: <umbrella> | new sub-page: <new-sub-slug>`.
  3. **Stale entries** — if step 1 has an entry whose product slug does NOT appear in any `## Product:` section of the new raw, keep it in `products` anyway (so its sub-page is preserved and re-rendered with whatever about-text remains, or left unchanged if no source material survives). Log INFO: `refresh: <umbrella> | sub-page <sub-slug> retained — product not present in new discovery; remove manually if upstream truly dropped it`.

  Pass the merged `products` list to ingest. Step 2c writes/updates the umbrella body (with the updated `subpages:` list reflecting any new subs) and each sub-page body. Pass `companion_slug = null`.

  After ingest returns, append a refresh log entry to `wiki/log.md`: include in the log the list of newly-created sub-pages (if any) so the change is auditable.

**Standalone page:**
- If content is identical → record `refresh: <slug> (no change)`.
- If content differs → overwrite `raw_file_path`, run ingest steps 2–5 and 7. Pass `companion_slug = null` and `companion_raw_file_path = null` and `products = []` (refresh never promotes to unified or multi-product).

In either case, if content changed, append to `wiki/log.md` immediately below the heading (newest at top):
```
## <today> | refresh | <slug> | content updated

- Updated: wiki/sources/<slug>.md, wiki/index.md, wiki/overview.md, wiki/log.md
- Raw: <comma-separated list of changed raw paths>
```

### 5. Update inbox line

- Remove `<!-- refresh -->` from the line.
- Append `<!-- refreshed <today> -->`.
- Preserve the existing `[ ]` / `[x]` state.
- Write the updated `inbox.md`.
- **Do not** run `git commit` or `git push` (see the wiki’s `AGENTS.md` **Git — never auto-commit**).

Append `{pass: 2, url, slug, outcome: refreshed | no-change}` to run log.

---

## Post-run lint

If `auto_lint: batch`: read `<skill-dir>/lint.md` and run the full lint. Include the lint report in the run output below.

If `auto_lint: never` or `per-ingest`: skip lint. Per-ingest lint is suppressed when running in batch mode — lint fires once at the end (`batch`) or not at all (`never`). It never fires per-item inside `run`.

---

## Summary report

Print:

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

---

## Notes

- **Idempotency:** items remain under `## Pending` until successfully ingested. A crashed run can be safely re-run — it picks up from the first item still under `## Pending`.
- **No agent commits:** ingest and refresh never run `git commit`—the human commits after review.
- **`<!-- skip -->` is persistent:** the tag remains on the line and `run` skips it on every subsequent invocation. Remove the tag manually to process the item.
- **Partial raw content on crash:** if a run crashes mid-fetch, the partial raw file (if any) will be overwritten on the next run's re-fetch — no manual cleanup needed.
