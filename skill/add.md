# add — single-source ingest

> **Skill directory note:** This file is in the skill directory (e.g. `<skill-dir>/`, `~/.claude/skills/pin-llm-wiki/`, `~/.copilot/skills/pin-llm-wiki/`, or `~/.cursor/skills/pin-llm-wiki/`). All `templates/` and sibling-file paths below are relative to that same directory. Use whichever path applies to the tool that loaded this skill.

## Guard

Check whether `.pin-llm-wiki.yml` exists in the current working directory. If not, stop:
> "No wiki found here (`.pin-llm-wiki.yml` missing). Run `/pin-llm-wiki init` to scaffold one first."

---

## Setup

**Read config:**
Read `.pin-llm-wiki.yml` and extract: `detail_level`, `source_types`, `auto_mark_complete`, `auto_lint`.

**Parse the URL:**
The URL is the first argument after `/pin-llm-wiki add`. Also capture any inline tags that follow the URL in the invocation: `<!-- detail:X -->`, `<!-- branch:X -->`, `<!-- clone -->`.

---

## Source type detection

Match the URL (in order):

| Pattern | Type |
|---|---|
| `github.com/<org>/<repo>` — exactly two non-empty path segments | `github` |
| `github.com/<org>/<repo>/<...>` — any additional path segments (for example `/tree/...`, `/blob/...`, `/issues/...`) | `web` |
| `youtube.com/watch?v=` or `youtu.be/<id>` | `youtube` |
| anything else | `web` |

If the detected type is not in `source_types` from config, note the mismatch in the final confirmation summary but proceed anyway — the user has explicitly requested this URL.

---

## Inbox check

Read `inbox.md`.

- **URL already under `## Completed`:** stop.
  > "This URL has already been ingested (found under ## Completed). To re-fetch, add `<!-- refresh -->` to its line and run `/pin-llm-wiki run`."
- **URL already under `## Pending`:** use the existing line as-is (including any tags it has). Do not append a duplicate.
- **URL not in `inbox.md`:** append a new line to `## Pending`:
  `- [ ] <url> <any tags from the invocation args>`

---

## Effective detail level and tags

Locate the inbox line for this URL. Extract any tags:

- `<!-- detail:X -->` — overrides `detail_level` for this source only. X must be `brief`, `standard`, or `deep`.
- `<!-- branch:X -->` — GitHub only; overrides the branch detected from the repo.
- `<!-- clone -->` — GitHub only; effective only at `deep`; triggers a full `git clone`.
- `<!-- companion:github.com/<org>/<repo> -->` — Web only; skip GitHub discovery, use this exact repo as the companion.
- `<!-- no-companion -->` — Web only; suppress companion GitHub fetch even if a repo is detected.

**Effective detail level** = `<!-- detail:X -->` tag if present, else `detail_level` from config.

**Companion context** (web sources only):
- `companion_override_url` = URL from `<!-- companion:... -->` tag, or null.
- `suppress_companion` = true if `<!-- no-companion -->` is present, else false.

---

## Slug and raw path

Derive slug and raw file path (except YouTube — finalized after fetch; see below):

**GitHub:**
- Slug: `<org>-<repo>` (extracted from URL path segments)
- Raw path: `raw/github/<org>-<repo>.md`

**YouTube:**
- Video ID: parse from `?v=<id>` (youtube.com) or path `/<id>` (youtu.be)
- Title slug: `<title>` lowercased, spaces and special chars replaced with hyphens, truncated at 40 chars — **requires `yt-dlp --dump-json` output from fetch step 1**
- Full slug: `<video-id>-<title-slug>` — **finalize after fetch step 1, before writing the raw file**
- Raw path: `raw/youtube/<video-id>-<title-slug>.md`

**Web:**
- Domain: extract hostname from URL, strip `www.` prefix. Preserve subdomains (e.g. `docs.langchain.com` stays as `docs.langchain.com` — do not collapse to `langchain.com`).
- **Default slug:** the domain string
- **GitHub non-root page special case:** if the URL is `github.com/<org>/<repo>/<...>`, derive the slug as `<org>-<repo>-<path-slug>`, where `<path-slug>` is the remaining path joined with hyphens and normalized to kebab-case. Example: `https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking` → `modelcontextprotocol-servers-tree-main-src-sequentialthinking`
- Raw path: `raw/web/<slug>.md` — always one file per ingest, regardless of detail level. Deep mode no longer produces per-page directories. In deep multi-product mode the single raw file contains `## Product:` sections that drive sub-page creation during ingest.

---

## Fetch

Read the protocol file for the detected type and follow it exactly:

- **GitHub:** read `<skill-dir>/templates/protocols/github.md`
- **YouTube:** read `<skill-dir>/templates/protocols/youtube.md`
- **Web:** read `<skill-dir>/templates/protocols/web.md`

Use the effective detail level throughout. Apply `<!-- branch:X -->` and `<!-- clone -->` tags (GitHub only).

**GitHub non-root page special case:** when the detected type is `web` because the URL is `github.com/<org>/<repo>/<...>`, treat it as a **single-page web capture**. Fetch only the exact URL. Skip `llms.txt`, docs discovery, and companion GitHub discovery regardless of detail level.

**Fetch failure handling:**

- **YouTube, no transcript available:** flag the inbox line with `<!-- fetch-failed:no-transcript -->`. Leave it in `## Pending` (do not move to Completed, do not mark `[x]`). Report to user and stop — do not proceed to ingest.
- **200k token guard:** if cumulative input tokens for this source approach 200k during fetch, halt and ask the user whether to continue or abort.
- **Other fetch error:** report the error, leave the inbox line in `## Pending`, stop.

---

## Companion fetch

**Only runs when:** `type = web` AND `companion_github_url` (returned by the web fetch protocol step 7) is non-null AND `suppress_companion` is false AND `products` (from web fetch step 5) is empty or has fewer than 2 entries. In deep multi-product mode (`len(products) >= 2`), companion fetch is skipped entirely — the protocol returns `companion_github_url = null`.

If `companion_override_url` is set, use it as `companion_github_url` instead of what the protocol discovered.

**Guard: self-loop** — if `companion_github_url` resolves to `github.com/<org>/<repo>` and the inbox URL itself is `https://github.com/<org>/<repo>` (same repo), discard the companion and set `companion_github_url = null`. Skip the companion fetch.

Steps:
1. Derive `companion_slug` = `<org>-<repo>` from `companion_github_url`.
2. Derive `companion_raw_file_path` = `raw/github/<org>-<repo>.md`.
3. Read `<skill-dir>/templates/protocols/github.md` and fetch `github.com/<org>/<repo>`. Use the same `effective_detail_level`. Apply any `<!-- branch:X -->` tag from the inbox line (the companion inherits it).
4. Write `companion_raw_file_path`.
5. Update `raw/github/README.md`: add a row for the companion repo (or update in-place if already present).

**Failure handling:**
- Fetch error (repo not found, rate limit, etc.): log `WARN: companion fetch failed for <companion_github_url> — <reason>`. Set `companion_slug = null`. Proceed with web-only ingest.
- 200k token guard: if adding the companion fetch would exceed the cumulative budget, ask the user to choose: (a) proceed companion-only at `brief`, (b) skip companion, or (c) abort. Do not silently skip.

---

## Ingest

Once the raw file(s) are written, read `<skill-dir>/ingest.md` and follow its instructions.

Carry this context into ingest:

| Variable | Value |
|---|---|
| `slug` | derived above (YouTube: finalized after fetch step 1) |
| `type` | `github` / `youtube` / `web` |
| `raw_file_path` | path computed above |
| `effective_detail_level` | tag override or config default |
| `auto_mark_complete` | from config |
| `today` | current date `YYYY-MM-DD` |
| `companion_slug` | `<org>-<repo>` if companion fetch succeeded; null otherwise (always null in deep multi-product mode) |
| `companion_raw_file_path` | `raw/github/<org>-<repo>.md` if companion fetch succeeded; null otherwise |
| `products` | list returned by web fetch step 5 (web sources only). Empty/null when only one product was discovered or detection is not applicable. ≥2 entries triggers the multi-product ingest branch. |

---

## Post-ingest

- **`auto_lint: per-ingest`:** read `<skill-dir>/lint.md` and run the full lint. Include the lint report in the output below.
- Print confirmation:

```
Ingested: <url>

  Type:        <github | youtube | web>
  Slug:        <slug>
  Raw:         <raw_file_path>
  Wiki page:   wiki/sources/<slug>.md
  Detail:      <effective_detail_level>
  Companion:   raw/github/<org>-<repo>.md   ← only when companion fetch succeeded
  Products:    <product1>, <product2>, ...   ← only when deep multi-product mode produced subs
  Sub-pages:   wiki/sources/<slug>-<product1>.md, wiki/sources/<slug>-<product2>.md, ...

Updated: wiki/index.md, wiki/overview.md, wiki/log.md, raw/<type>/README.md, inbox.md
```

If companion fetch was attempted but failed: `  Companion:   fetch failed (<reason>) — web-only page produced`.
If the detected type was not in `source_types`, append: `  Note: source type <type> is not in this wiki's source_types config.`
If multi-product mode was triggered, list all sub-page paths under `Sub-pages:`.

Do not run `git commit`—see the wiki’s `AGENTS.md` **Git — never auto-commit** (suggested message for the human: `ingest: <slug>`).
