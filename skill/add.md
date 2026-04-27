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

**Effective detail level** = `<!-- detail:X -->` tag if present, else `detail_level` from config.

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
- Slug: the domain string
- Raw path: `raw/web/<domain>.md` (brief/standard) or `raw/web/<domain>/` (deep)

---

## Fetch

Read the protocol file for the detected type and follow it exactly:

- **GitHub:** read `<skill-dir>/templates/protocols/github.md`
- **YouTube:** read `<skill-dir>/templates/protocols/youtube.md`
- **Web:** read `<skill-dir>/templates/protocols/web.md`

Use the effective detail level throughout. Apply `<!-- branch:X -->` and `<!-- clone -->` tags (GitHub only).

**Fetch failure handling:**

- **YouTube, no transcript available:** flag the inbox line with `<!-- fetch-failed:no-transcript -->`. Leave it in `## Pending` (do not move to Completed, do not mark `[x]`). Report to user and stop — do not proceed to ingest.
- **200k token guard:** if cumulative input tokens for this source approach 200k during fetch, halt and ask the user whether to continue or abort.
- **Other fetch error:** report the error, leave the inbox line in `## Pending`, stop.

---

## Ingest

Once the raw file is written, read `<skill-dir>/ingest.md` and follow its instructions.

Carry this context into ingest:

| Variable | Value |
|---|---|
| `slug` | derived above (YouTube: finalized after fetch step 1) |
| `type` | `github` / `youtube` / `web` |
| `raw_file_path` | path computed above |
| `effective_detail_level` | tag override or config default |
| `auto_mark_complete` | from config |
| `today` | current date `YYYY-MM-DD` |

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

Updated: wiki/index.md, wiki/overview.md, wiki/log.md, raw/<type>/README.md, inbox.md
```

If the detected type was not in `source_types`, append: `  Note: source type <type> is not in this wiki's source_types config.`

Do not run `git commit`—see the wiki’s `AGENTS.md` **Git — never auto-commit** (suggested message for the human: `ingest: <slug>`).
