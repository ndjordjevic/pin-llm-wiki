### Web fetch protocol

**Trigger:** inbox URL does not match github.com or youtube patterns.
**Tool:** `WebFetch` (primary). Fallbacks: Jina Reader (`r.jina.ai/<url>`) or headless browser only if WebFetch returns a content-free skeleton.

**Special case — GitHub non-root pages:** when the URL is `github.com/<org>/<repo>/<...>` (for example `/tree/...`, `/blob/...`, `/issues/...`), this protocol runs in **single-page mode**. The intent is to capture only the requested GitHub page, not the whole repository.

Steps:

1. **Check whether the URL is a GitHub non-root page.**
   - **If yes:** skip steps 2–6 below entirely. Fetch only the exact URL and store it as a one-page raw capture. Do **not** fetch `llms.txt`, do **not** discover docs pages, and do **not** discover a companion GitHub repo or run product discovery. Return `companion_github_url = null`, `products = []`. Skip ahead to step 8 (write).
   - **If no:** continue with step 2.
2. **Check `<domain>/llms.txt`** (fetch `https://<domain>/llms.txt`). If present, capture its full content — it supplements but does **not** replace steps 3–5.
3. **Fetch the landing page** (`<final-url>`).
4. **Discover docs pages** — always, regardless of whether llms.txt was found. Try `/docs`, `/documentation`, `/guide`, `sitemap.xml`, and the conventional subdomain `docs.<domain>` (in that order). Stop at the first that returns real content.
   - At `brief`: skip docs entirely.
   - At `standard`: fetch the docs index page and ~4–10 key pages (product overviews, getting-started, architecture, reference).
   - At `deep`: fetch the docs index page and ~10–25 key pages, then run product discovery (step 5) and per-product docs fetch (step 6).
5. **Product discovery** (`deep` only — skipped at `brief`/`standard` and in single-page mode). The goal is to determine whether this site presents **multiple distinct products** that each merit their own wiki source page.

   Scan, in priority order:
   a. The docs nav/landing of the docs site discovered in step 4 — top-level sections that point to distinct product subsections (for example `docs.langchain.com/langchain/...`, `docs.langchain.com/langgraph/...`, `docs.langchain.com/langsmith/...`).
   b. The landing page hero/nav and footer for product-card lists, "Products" menus, or repeated `<product>.<domain>` subdomains.
   c. The llms.txt content from step 2 — distinct product entries point to distinct products.
   d. GitHub repo URLs referenced anywhere in the captured content — multiple repo-root URLs under the same `<org>` are strong evidence of multiple products (for example `github.com/langchain-ai/langchain`, `github.com/langchain-ai/langgraph`, `github.com/langchain-ai/langsmith`, `github.com/langchain-ai/deepagents`).

   **Acceptance threshold (must hold for a candidate to count as a product):**
   - The candidate has its own dedicated docs subsection (its own URL path under the docs site or its own subdomain), **OR** its own distinct repo-root GitHub URL under the same org.
   - The candidate is **not** a generic site section like `Pricing`, `Features`, `Solutions`, `Customers`, `Blog`, `About`, `Careers`, `Contact`, `Login`, `Sign up`, `Changelog`, `Roadmap`, `Status`, `Legal`, `Terms`, `Privacy`. Reject these by name even if they appear in nav.

   **Output:** a list `products`, each entry: `{ name, slug, deep_link_url?, docs_url?, repo_url? }`.
   - `name` — display name, e.g. `LangGraph`.
   - `slug` — kebab-case product identifier, e.g. `langgraph`. Used in sub-page slug `<domain>-<slug>`.
   - `deep_link_url` — product-specific page on the source site if one exists (e.g. `https://www.langchain.com/langgraph`); null otherwise.
   - `docs_url` — entry point into this product's docs subsection if discovered.
   - `repo_url` — companion GitHub repo URL if one was matched.

   **Multi-product trigger:** `len(products) >= 2`. If `len(products) < 2`, set `products = []` and proceed in single-product deep mode (step 6 skipped, step 7 simplified).
6. **Per-product docs fetch** (deep multi-product only — runs only when `len(products) >= 2`).

   For each entry in `products`, fetch ~5–10 key docs pages from its `docs_url` subsection: overview / getting started / key concepts / API or reference / when-to-use. Hold each set in memory keyed by product slug.

   If a product was discovered via repo URL only (no `docs_url`), skip per-product docs fetch for that product — its sub-page will be sparser, and the human can promote it to a full unified ingest later via `companion:` override on a separate `add` call.
7. **Companion GitHub repo discovery.**

   **Skipped entirely in deep multi-product mode** (`len(products) >= 2` from step 5): immediately set `companion_github_url = null` and proceed to step 8. The umbrella does not get a single companion repo; each product's `repo_url` (if any) is recorded in `products[*].repo_url` for the human to ingest separately if desired.

   In all other modes (brief, standard, single-product deep), scan the collected content in this priority order:
   a. The llms.txt content captured in step 2 (look for any `github.com/<org>/<repo>` line).
   b. The landing page's first ~500 characters (hero section, navigation bar).
   c. Any anchor text on the landing page containing `github.com/<org>/<repo>` (footer, "open source", "view on GitHub" links).

   Accept a URL only when it has exactly two non-empty path segments after `github.com/` and is a repo root — reject `/tree/`, `/blob/`, `/orgs/`, `/issues/`, `/pulls/`, etc.

   **Tie-break:** when multiple repo URLs appear, prefer the one whose `<org>` is most similar to the domain root (e.g. `paperclip.ing` → prefer `paperclipai/*`). If still tied, take the first in priority order.

   Return the result as `companion_github_url` (a full URL string or `null`). **Do not fetch the repo here** — the caller (`add.md` / `run.md`) decides whether to fetch, applying any inbox-line tag overrides (`<!-- companion:... -->`, `<!-- no-companion -->`) before doing so.
8. **Compile and write the raw file.** Always one file per ingest at `raw/web/<slug>.md` — no per-page directories. The file format is described below; deep multi-product mode adds `## Product: <name>` sections.
9. **Follow redirects; log the final URL** to the raw file — not the original inbox URL. Stale domains silently redirect.
10. Respect `robots.txt`. Set a descriptive user agent. Rate-limit between requests.

**Returned to caller:** `companion_github_url`, `products` (list, possibly empty), `final_url`, `pages_count`. The caller (`add.md` / `run.md` / refresh) reads `products` and `companion_github_url` to decide which ingest branch to use.

**Guard:** if the cumulative crawl would exceed 200k input tokens, halt and surface to user before proceeding. In deep multi-product mode this is especially important — 4 products × 10 docs pages each will brush the limit; if the budget is tight, prefer fewer pages per product over fewer products.

**Raw file format** (`raw/web/<slug>.md`):
```
# <slug>

## Fetch log
- Inbox URL: <original url>
- Final URL: <final url after redirects>
- Fetched: <YYYY-MM-DD>
- Pages: <N>
- Mode: <single-page | brief | standard | deep | deep-multi-product>
- Products discovered: <N>     ← present only when Mode is deep or deep-multi-product
- Products: <comma-separated slugs>     ← present only when N >= 1

## llms.txt (if present)
<full content>

## Landing page — <final-url>
<page content>

## Docs — <docs-index-url>     ← present at standard and deep
<docs index page content>

## <Page title> — <url>     ← additional docs/key pages at standard and deep (single-product)
<page content>
...

## Product: <Product Name>     ← present per-product in deep multi-product mode only
- Slug: <product-slug>
- Deep link: <deep_link_url or "n/a">
- Docs URL: <docs_url or "n/a">
- Companion repo: <repo_url or "n/a">

### About
<short description from landing/hero/docs intro for this product>

### Docs — <docs_url>
<fetched docs index for this product>

### <Doc page title> — <url>
<fetched docs page content>
...
```

`Pages: <N>` counts every captured item in the compiled raw file, including `llms.txt` when present. For example, `llms.txt + landing page + 4 docs pages` means `Pages: 6`. In deep multi-product mode, sum across all `## Product:` sections too.

In **GitHub non-root single-page mode**, the compiled raw file contains only:
```
# <slug>

## Fetch log
- Inbox URL: <original url>
- Final URL: <final url after redirects>
- Fetched: <YYYY-MM-DD>
- Pages: 1
- Mode: single-page

## Page — <final-url>
<page content>
```

**README.md row format** (`raw/web/README.md`):
`| raw/web/<slug>.md | <slug> | <pages-fetched> | <YYYY-MM-DD> | |`
