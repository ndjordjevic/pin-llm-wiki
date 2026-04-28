### Web fetch protocol

**Trigger:** inbox URL does not match github.com or youtube patterns.
**Tool:** `WebFetch` (primary). Fallbacks: Jina Reader (`r.jina.ai/<url>`) or headless browser only if WebFetch returns a content-free skeleton.

Steps:

1. **Check `<domain>/llms.txt`** (fetch `https://<domain>/llms.txt`). If present, capture its full content — it supplements but does **not** replace steps 2–3.
2. **Fetch the landing page** (`<final-url>`).
3. **Discover docs pages** — always, regardless of whether llms.txt was found. Try `/docs`, `/documentation`, `/guide`, `sitemap.xml` (in that order). Stop at the first that returns real content. At `standard` and `deep`, fetch the docs index page and ~4–10 key pages (product overviews, getting-started, architecture, reference). At `brief`, skip this step.
4. **Discover companion GitHub repo** — scan the collected content in this priority order:
   a. The llms.txt content captured in step 1 (look for any `github.com/<org>/<repo>` line).
   b. The landing page's first ~500 characters (hero section, navigation bar).
   c. Any anchor text on the landing page containing `github.com/<org>/<repo>` (footer, "open source", "view on GitHub" links).

   Accept a URL only when it has exactly two non-empty path segments after `github.com/` and is a repo root — reject `/tree/`, `/blob/`, `/orgs/`, `/issues/`, `/pulls/`, etc.

   **Tie-break:** when multiple repo URLs appear, prefer the one whose `<org>` is most similar to the domain root (e.g. `paperclip.ing` → prefer `paperclipai/*`). If still tied, take the first in priority order.

   Return the result as `companion_github_url` (a full URL string or `null`). **Do not fetch the repo here** — the caller (`add.md` / `run.md`) decides whether to fetch, applying any inbox-line tag overrides (`<!-- companion:... -->`, `<!-- no-companion -->`) before doing so.

5. Depth by detail level:
   - `brief`: llms.txt (if any) + landing page only.
   - `standard`: llms.txt (if any) + landing + docs index + ~4–10 key pages.
   - `deep`: full crawl within domain; one file per page at `raw/web/<domain>/<page-slug>.md`.
6. **Follow redirects; log the final URL** to the raw file — not the original inbox URL. Stale domains silently redirect.
7. Respect `robots.txt`. Set a descriptive user agent. Rate-limit between requests.
8. Save to `raw/web/<domain>.md` (one compiled file at `brief`/`standard`). At `deep`, use `raw/web/<domain>/<page-slug>.md` per-page.

**Guard:** if the full crawl would exceed 200k input tokens, halt and surface to user before proceeding.

**Raw file format** (`raw/web/<domain>.md`):
```
# <domain>

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

**README.md row format** (`raw/web/README.md`):
`| raw/web/<domain>.md | <domain> | <pages-fetched> | <YYYY-MM-DD> | |`
