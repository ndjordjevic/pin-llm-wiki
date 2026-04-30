### Common protocol — URL parsing, slug derivation, inbox tags, companion fetch

Shared subroutines used by `run.md` and `queue.md`. Read the relevant section instead of inlining.

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
| `<!-- skip -->` | `run` skips the line on every invocation until the tag is removed. |
| `<!-- refresh -->` | Persists in `## Completed`; triggers Pass 2 refresh on next `run`. |
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
