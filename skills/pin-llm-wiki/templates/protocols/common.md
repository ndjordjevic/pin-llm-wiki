### Common protocol — URL parsing, slug derivation, inbox tags, companion fetch

Shared subroutines used by `ingest.md` and `queue.md`. Read the relevant section instead of inlining.

---

## Source-type detection

Match the URL in this order:

| Pattern | Type |
|---|---|
| `github.com/<org>/<repo>` — exactly two non-empty path segments | `github` |
| `github.com/<org>/<repo>/<...>` — any additional path segments (`/tree/...`, `/blob/...`, `/issues/...`) | `web` (single-page) |
| `youtube.com/watch?v=` or `youtu.be/<id>` | `youtube` |
| anything else | `web` |

If the detected type is not in `source_types` from config, note the mismatch in the final confirmation but proceed anyway — the user explicitly requested this URL.

---

## Pending URL identity (duplicate detection)

Use this normalization when deciding whether two pending inbox lines refer to the **same** source (for deduplicating work and consolidating `## Completed`).

1. Extract the URL token from the inbox line (first URL-shaped token after `- [ ]` / `- [x]`).
2. Trim ASCII whitespace around the URL string.
3. Parse as a URL. If parsing fails, treat the raw trimmed string as the identity (no merging with other lines).
4. **Scheme + host:** lowercase both.
5. **Host-only exception — YouTube:** if the host is `youtu.be` or ends with `youtube.com` (e.g. `www.youtube.com`, `m.youtube.com`), reduce to a **canonical key**:
   - `youtu.be/<video-id>` → key `youtube:<video-id>` (path segment only, ignore query).
   - `youtube.com/...` → extract `v=` from query or `list=` if needed; for standard watch URLs use key `youtube:<v>`.
   - Two lines that resolve to the same `youtube:<video-id>` are duplicates.
6. **All other URLs:** identity key = string `url:` + normalized serialization: scheme + `://` + host + path with trailing `/` removed except when path is `/`, + sorted query string if present (standard `key=value` pairs; omit empty query). Strip `#fragment`.
7. Two pending lines are **duplicates** iff their identity keys are equal.

`queue` may still refuse a second append when it finds the same raw URL string already in Pending; humans can still paste duplicate lines manually — `ingest` uses this section to merge them.

---

## Slug and raw-path derivation

**GitHub:**
- Slug: `<org>-<repo>`
- Raw path: `raw/github/<org>-<repo>.md`

**YouTube:**
- Video ID from URL (`?v=<id>` or `youtu.be/<id>`)
- Title slug: lowercase title, spaces/special chars → hyphens, truncate at 40 chars — **requires `yt-dlp --dump-json` output; finalize after fetch step 1, before writing the raw file**
- Full slug: `<video-id>-<title-slug>`
- Raw path: `raw/youtube/<video-id>-<title-slug>.md`

**Web:**
- Domain: hostname with `www.` stripped; preserve subdomains (e.g. `docs.langchain.com` stays as `docs.langchain.com`)
- Slug: the domain string
- Raw path: `raw/web/<slug>.md` — always one file per ingest, regardless of detail level

**Web — X/Twitter status post** (host is `x.com` or `twitter.com` and path matches `/<user>/status/<id>` with optional trailing segments like `/photo/1`):
- Slug: `<host>-<user>-<title-slug>` (lowercase host preserved as `x.com` or `twitter.com`)
- Title-slug derivation — **requires fetched post text; finalize after the fetch step, before writing the raw file** (mirrors YouTube):
  1. Take the tweet body text (the quoted text after `<DisplayName> on X:`); strip surrounding quotes and the trailing ` / X` site suffix if present.
  2. **First sentence only** — split on `.`, `?`, `!` (treating `.` inside known acronyms like `CLAUDE.md`, `e.g.`, `i.e.` as non-terminal: don't split when the period is preceded by a single uppercase letter or a recognized abbreviation and followed by a non-space). Keep just the first sentence.
  3. **Strip apostrophes** (`'` and `'`) by deletion, not hyphenation: `Karpathy's` → `karpathys` (not `karpathy-s`).
  4. Lowercase; replace any remaining run of non-alphanumeric characters with a single `-`; trim leading/trailing `-`.
  5. **Drop stopwords** from this exact list (split on `-`, drop matches, rejoin): `a, an, the, of, from, to, in, on, for, by, with, and, or, but, as, at`.
  6. Truncate at **50 chars** at the last `-` boundary (no mid-word cuts).
  7. **Fallback** — if the post body is empty, image/video-only, or yields a title-slug shorter than 8 chars after step 6, use `status-<id>` instead.
- Example: `https://x.com/mnilax/status/2053116311132155938` with body "Karpathy's 4 CLAUDE.md rules cut Claude mistakes from 41% to 11%. After 30 codebases, I added 8 more" → `x.com-mnilax-karpathys-4-claude-md-rules-cut-claude-mistakes`
- Raw path: `raw/web/<slug>.md`
- Treated as a **single-page web capture**: fetch only the exact status URL (via Jina reader fallback if direct fetch is blocked); skip llms.txt, docs discovery, and companion discovery regardless of detail level. A companion GitHub repo may still be fetched if a `github.com/<org>/<repo>` URL appears in the post body and `suppress_companion` is false.

**GitHub non-root page** (URL is `github.com/<org>/<repo>/<...>`):
- Slug: `<org>-<repo>-<path-slug>` where `<path-slug>` is the remaining path joined with hyphens, kebab-cased
- Example: `https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking` → `modelcontextprotocol-servers-tree-main-src-sequentialthinking`
- Raw path: `raw/web/<slug>.md`
- Treated as a **single-page web capture**: fetch only the exact URL; skip llms.txt, docs discovery, and companion discovery regardless of detail level.

---

## Inbox-line tag parsing

After the URL on an inbox line, any of these HTML comments may appear:

| Tag | Meaning |
|---|---|
| `<!-- detail:X -->` | X ∈ `brief`/`standard`/`deep`. Overrides `detail_level` for this source only. |
| `<!-- branch:X -->` | GitHub only. Override default branch detection. |
| `<!-- clone -->` | GitHub only; effective only at `deep`; triggers full `git clone`. |
| `<!-- companion:github.com/<org>/<repo> -->` | Web only. Skip GitHub discovery; use this exact repo as companion. |
| `<!-- no-companion -->` | Web only. Suppress companion GitHub fetch even if a repo is detected. |
| `<!-- skip -->` | `ingest` skips the line on every invocation until the tag is removed. |
| `<!-- refresh -->` | Persists in `## Completed`; triggers Pass 2 refresh on next `ingest`. |
| `<!-- note: <text> -->` | Freeform rationale. Preserved as-is; ignored by all subcommands. |
| `<!-- fetch-failed:<reason> -->` | Auto-added when fetch fails (e.g. `no-transcript`). |
| `<!-- ingested YYYY-MM-DD -->` | Auto-added when the line moves to `## Completed`. |
| `<!-- refreshed YYYY-MM-DD -->` | Auto-added on successful Pass 2 refresh. |

Derived values:
- **Effective detail level** = `<!-- detail:X -->` if present, else `detail_level` from config.
- **`companion_override_url`** = URL from `<!-- companion:... -->` tag, or null.
- **`suppress_companion`** = true if `<!-- no-companion -->` is present, else false.

---

## Companion-fetch sub-protocol (web sources)

**Runs only when:** `type = web` AND web protocol step 7 returned non-null `companion_github_url` AND `suppress_companion` is false AND web protocol step 5 returned `len(products) < 2` (deep multi-product mode skips companion fetch entirely).

If `companion_override_url` is set, use it as `companion_github_url` instead of the discovered value.

**Self-loop guard:** if `companion_github_url` resolves to the same repo as the inbox URL, discard it (set `companion_github_url = null`, skip).

Steps:
1. Derive `companion_slug = <org>-<repo>` and `companion_raw_file_path = raw/github/<org>-<repo>.md`.
2. Read `<skill-dir>/templates/protocols/github.md`; fetch `github.com/<org>/<repo>` at `effective_detail_level`. Inherit any `<!-- branch:X -->` tag.
3. Write `companion_raw_file_path`.
4. Update `raw/github/README.md`: add row or update in-place.

**Failure handling:**
- Fetch error → log `WARN: companion fetch failed for <url> — <reason>`, set `companion_slug = null`, proceed with web-only ingest.
- 200k token guard would be exceeded → ask user to choose: (a) proceed companion-only at `brief`, (b) skip companion, or (c) abort.
