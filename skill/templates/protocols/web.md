### Web fetch protocol

**Trigger:** inbox URL does not match github.com or youtube patterns.
**Tool:** `WebFetch` (primary). Fallbacks: Jina Reader (`r.jina.ai/<url>`) or headless browser only if WebFetch returns a content-free skeleton.

Steps:

1. **Check `<domain>/llms.txt` first** (fetch `https://<domain>/llms.txt`). If present, it provides a structured concept index for the site — this often replaces the full crawl.
2. If no `llms.txt`: fetch the landing page and discover docs via `/docs`, `/documentation`, `/guide`, `sitemap.xml` links.
3. Depth by detail level:
   - `brief`: landing page only (or llms.txt if present).
   - `standard`: llms.txt (if any) + landing + docs index + ~4–10 key pages (product overviews, getting-started, architecture).
   - `deep`: full crawl within domain; one file per page at `raw/web/<domain>/<page-slug>.md`.
4. **Follow redirects; log the final URL** to the raw file — not the original inbox URL. Stale domains silently redirect.
5. Respect `robots.txt`. Set a descriptive user agent. Rate-limit between requests.
6. Save to `raw/web/<domain>.md` (one compiled file at `brief`/`standard`). At `deep`, use `raw/web/<domain>/<page-slug>.md` per-page.

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
