### Web fetch protocol

**Trigger:** inbox URL does not match github.com or youtube patterns.
**Tool:** `WebFetch` (primary). Fallbacks: Jina Reader (`r.jina.ai/<url>`) or headless browser only if WebFetch returns a content-free skeleton.

**Special case — GitHub non-root pages:** when the URL is `github.com/<org>/<repo>/<...>` (for example `/tree/...`, `/blob/...`, `/issues/...`), this protocol runs in **single-page mode**. The intent is to capture only the requested GitHub page, not the whole repository.

Steps:

1. **Check whether the URL is a GitHub non-root page.**
   - **If yes:** skip steps 2-4 below entirely. Fetch only the exact URL and store it as a one-page raw capture. Do **not** fetch `llms.txt`, do **not** discover docs pages, and do **not** discover a companion GitHub repo. Return `companion_github_url = null`.
   - **If no:** continue with step 2.
2. **Check `<domain>/llms.txt`** (fetch `https://<domain>/llms.txt`). If present, capture its full content — it supplements but does **not** replace steps 3-4.
3. **Fetch the landing page** (`<final-url>`).
4. **Discover docs pages** — always, regardless of whether llms.txt was found. Try `/docs`, `/documentation`, `/guide`, `sitemap.xml` (in that order). Stop at the first that returns real content. At `standard` and `deep`, fetch the docs index page and ~4–10 key pages (product overviews, getting-started, architecture, reference). At `brief`, skip this step.
5. **Discover companion GitHub repo** — scan the collected content in this priority order:
   a. The llms.txt content captured in step 2 (look for any `github.com/<org>/<repo>` line).
   b. The landing page's first ~500 characters (hero section, navigation bar).
   c. Any anchor text on the landing page containing `github.com/<org>/<repo>` (footer, "open source", "view on GitHub" links).

   Accept a URL only when it has exactly two non-empty path segments after `github.com/` and is a repo root — reject `/tree/`, `/blob/`, `/orgs/`, `/issues/`, `/pulls/`, etc.

   **Tie-break:** when multiple repo URLs appear, prefer the one whose `<org>` is most similar to the domain root (e.g. `paperclip.ing` → prefer `paperclipai/*`). If still tied, take the first in priority order.

   Return the result as `companion_github_url` (a full URL string or `null`). **Do not fetch the repo here** — the caller (`add.md` / `run.md`) decides whether to fetch, applying any inbox-line tag overrides (`<!-- companion:... -->`, `<!-- no-companion -->`) before doing so.

6. Depth by detail level:
   - `brief`: llms.txt (if any) + landing page only.
   - `standard`: llms.txt (if any) + landing + docs index + ~4–10 key pages.
   - `deep`: full crawl within domain; one file per page at `raw/web/<slug>/`.
   - **GitHub non-root single-page mode:** always capture only the exact page, regardless of detail level.
7. **Follow redirects; log the final URL** to the raw file — not the original inbox URL. Stale domains silently redirect.
8. Respect `robots.txt`. Set a descriptive user agent. Rate-limit between requests.
9. Save to `raw/web/<slug>.md` (brief/standard/single-page mode). At `deep`, use `raw/web/<slug>/` per-page.

**Guard:** if the full crawl would exceed 200k input tokens, halt and surface to user before proceeding.

**Raw file format** (`raw/web/<slug>.md`):
```
# <slug>

## Fetch log
- Inbox URL: <original url>
- Final URL: <final url after redirects>
- Fetched: <YYYY-MM-DD>
- Pages: <N>

## llms.txt (if present)
<full content>

## Landing page — <final-url>
<page content>

## <Page title> — <url>
<page content>
...
```

`Pages: <N>` counts every captured item in the compiled raw file, including `llms.txt` when present. For example, `llms.txt + landing page + 4 docs pages` means `Pages: 6`.

In **GitHub non-root single-page mode**, the compiled raw file contains only:
```
# <slug>

## Fetch log
- Inbox URL: <original url>
- Final URL: <final url after redirects>
- Fetched: <YYYY-MM-DD>
- Pages: 1

## Page — <final-url>
<page content>
```

**README.md row format** (`raw/web/README.md`):
`| raw/web/<slug>.md | <slug> | <pages-fetched> | <YYYY-MM-DD> | |`
