# queue — add URLs to the pending inbox without ingesting

(Skill-directory paths and the `.pin-llm-wiki.yml` Guard are defined in `SKILL.md`.)

## Purpose

`queue` lets any agent add one or more URLs to `inbox.md`'s `## Pending` section **without fetching or ingesting**. Use it to surface a potentially relevant source for later human review. Use `/pin-llm-wiki run <url>` instead when you actually want to ingest now (it auto-queues missing URLs and ingests in one step).

---

## Input

Accept one or more URLs from the invocation args (space-separated). Each URL may be followed by any of the inline tags listed in `<skill-dir>/templates/protocols/common.md` § Inbox-line tag parsing.

---

## Per-URL logic

For each URL:

### 1. Check inbox.md

Read `inbox.md`.

- **URL already under `## Completed`:** skip this URL. Report:
  > "`<url>` already ingested (under ## Completed). To re-fetch, add `<!-- refresh -->` to its line."
- **URL already under `## Pending`:** skip this URL. Report:
  > "`<url>` already queued (under ## Pending)."
- **URL not in `inbox.md`:** proceed to step 2.

### 2. Append to `## Pending`

Append the line to the `## Pending` section of `inbox.md`, immediately before the `## Completed` heading (or at the end of the section):

```
- [ ] <url> <any inline tags> <any note tag>
```

Do not fetch, do not ingest, do not move to Completed.

### 3. Re-read before next URL

`inbox.md` was just mutated. Re-read it before processing the next URL to avoid duplicate appends.

---

## Confirmation

After processing all URLs, print:

```
Queued for ingest — <wiki-domain> wiki
<today>

  Added:    N URL(s)
  Skipped:  N (already pending or completed)

Next step: run `/pin-llm-wiki run` to ingest all pending items,
           or `/pin-llm-wiki run <url>` to ingest a single item immediately.
```

List each added URL on its own indented line under "Added:".
List each skipped URL with its reason under "Skipped:".

---

## Notes

- `queue` never runs a fetch, writes a raw file, or touches any wiki page.
- Any agent may call `queue`. It is the only inbox mutation an agent may perform outside of `run` and `remove`.
- No agent commits — see SKILL.md Git policy.
