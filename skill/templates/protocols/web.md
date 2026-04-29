### Web fetch protocol

**Trigger:** inbox URL does not match github.com or youtube patterns.
**Tool:** `WebFetch` (primary). Fallbacks: Jina Reader (`r.jina.ai/<url>`) or headless browser only if WebFetch returns a content-free skeleton.

**Verbatim-capture rule (critical for product discovery):** WebFetch passes the page through a small summarizer model. Even with explicit "do not summarize" instructions, it may still paraphrase prose and silently drop "redundant" entries from product menus, nav lists, and structured catalogs — the exact signals product discovery (Step 5) depends on. The directive helps but is not a guarantee. Two rules follow:

1. **For HTML pages (landing page, docs index, individual docs pages):** every WebFetch prompt **must** include: *"Return the page content verbatim. Preserve every product name, navigation entry, link, and list item exactly as it appears. Do not summarize, paraphrase, deduplicate, or filter for relevance."*
2. **For plain-text structural catalogs (`llms.txt`, `sitemap.xml`):** do **not** use WebFetch — its summarizer will mangle the catalog. Fetch with `curl -sL <url>` via Bash and store the raw response. These files are the only fully reliable product-enumeration source, so they must survive intact.

**Special case — GitHub non-root pages:** when the URL is `github.com/<org>/<repo>/<...>` (for example `/tree/...`, `/blob/...`, `/issues/...`), this protocol runs in **single-page mode**. The intent is to capture only the requested GitHub page, not the whole repository.

Steps:

1. **Check whether the URL is a GitHub non-root page.**
   - **If yes:** skip steps 2–6 below entirely. Fetch only the exact URL and store it as a one-page raw capture. Do **not** fetch `llms.txt`, do **not** discover docs pages, and do **not** discover a companion GitHub repo or run product discovery. Return `companion_github_url = null`, `products = []`. Skip ahead to step 8 (write).
   - **If no:** continue with step 2.
2. **Check `<domain>/llms.txt`** — fetch with: `curl -sL https://<domain>/llms.txt -o /tmp/pin-llm-wiki-llmstxt-<slug>.txt`. **Do not** invoke WebFetch on llms.txt — the WebFetch summarizer mangles it. Always go through the on-disk file.

   After curl, `cat /tmp/pin-llm-wiki-llmstxt-<slug>.txt | wc -c` to verify a non-empty response. If empty / 404 / not-found-style HTML, treat llms.txt as absent and skip to step 3.

   **The on-disk file is the canonical capture.** When step 8 assembles the raw file, the `## llms.txt — <url>` section is produced by **reading** `/tmp/pin-llm-wiki-llmstxt-<slug>.txt` and inserting its contents verbatim. Do not retype the content from memory; do not summarize; do not "list relevant entries." If you find yourself paraphrasing the catalog, stop — read the on-disk file again and paste those bytes literally. Step 5 discovery operates on this raw section; if it has been summarized, DeepAgents-class entries are silently dropped and discovery can never recover them.

   llms.txt is the primary product-discovery signal in Step 5; every line must reach Step 5 unfiltered. llms.txt supplements but does **not** replace steps 3–5.
3. **Fetch the landing page** (`<final-url>`). Capture verbatim. In particular, preserve the literal text of the hero section, primary nav, "Products" / "Frameworks" menus, product cards, and footer link blocks — these enumerate products that may not appear anywhere else. Paraphrased summaries of these elements are insufficient for Step 5.
4. **Discover docs pages** — always, regardless of whether llms.txt was found. Try `/docs`, `/documentation`, `/guide`, `sitemap.xml`, and the conventional subdomain `docs.<domain>` (in that order). Stop at the first that returns real content. For `sitemap.xml`, fetch with `curl -sL` (it is a structural catalog like llms.txt). For HTML docs pages, use WebFetch with the verbatim directive — capture the full top-level navigation tree, every section heading and link, not a paraphrase. Top-level docs sections are the strongest product-discovery signal.
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

   **Sanity check (mandatory before accepting `products`).** This step is what protects against missed products. Skipping or shortcutting it is the most common cause of incomplete ingests. Run it explicitly:

   **Step 5a — Build the candidate set from llms.txt and sitemap.xml** (the curl-fetched ground truth):
   - Parse the curl output of `llms.txt` and `sitemap.xml`. Collect every URL.
   - For every URL on the docs host (`docs.<domain>` or `<domain>/docs/`), extract its path segments and emit candidates at **depths 1, 2, and 3** simultaneously. For example, the URL `https://docs.langchain.com/oss/python/deepagents/quickstart` emits three candidates: `oss`, `oss/python`, and `oss/python/deepagents`. Many sites nest products under generic prefixes like `/oss/`, `/api/`, `/docs/`, `/products/` — depth-1 enumeration alone will miss them.
   - For every URL on a separate `docs.<subdomain>.<domain>` or `<subdomain>.<domain>` host, the subdomain is also a candidate.
   - Also collect: section headings (lines starting with `## ` or `# `) from llms.txt — these are the curated product list and outrank any URL heuristic, every product-card / framework-card name from the landing page capture, every `github.com/<org>/<repo>` repo-root URL.

   **Step 5b — Identify product nodes.** A path candidate is a **product node** when it satisfies any of:
   - It appears as a `## ` or `# ` heading in llms.txt with associated URLs underneath (the strongest signal — trust llms.txt section headings as products by default).
   - It has its own coherent docs cluster: ≥3 distinct child URLs underneath, or includes conventional docs-page names like `/overview`, `/quickstart`, `/getting-started`, `/home`, `/concepts`, `/reference`.
   - It appears as a product card / framework card on the landing page.
   - It corresponds to a `github.com/<org>/<repo>` repo-root URL under the same org as other discovered products.

   Generic intermediate path nodes (`oss`, `python`, `javascript`, `api`, `docs`, `guide`) are **not** products on their own — they are namespace containers. Products live one or more levels under them.

   **Step 5c — Classify every candidate.** For each candidate from step 5a, classify as exactly one of:
   - **Product** — passes step 5b. Must appear in `products`. If absent, add it (derive `slug`, `docs_url`, `repo_url`, `deep_link_url` from where it appeared in the captures).
   - **Excluded section** — matches the rejection list by name (Pricing, Features, Solutions, Customers, Blog, About, Careers, Contact, Login, Sign up, Changelog, Roadmap, Status, Legal, Terms, Privacy, plus generic namespace containers like `oss`, `api`, `docs`).
   - **Sub-section of an existing product** — lives under a path already represented in `products` (e.g. `oss/python/langgraph/interrupts` lives under `oss/python/langgraph` which is the LangGraph product node).

   If any candidate falls into none of these three buckets, it was missed: add it to `products`. Repeat until every candidate is accounted for.

   **Step 5d — Audit trail (mandatory).** Append a `## Discovery audit` section to memory (will be written to the raw file in step 8) listing every candidate from step 5a and its classification. The audit makes the enumeration verifiable instead of "the agent says it ran the check." If the audit lists fewer products than llms.txt has top-level section headings, something was skipped.

   If the verbatim captures are too thin to enumerate (e.g. the landing page returned paraphrased prose despite the verbatim directive, or llms.txt was summarized away in step 2), refetch with a stricter prompt before continuing — do not classify candidates from a paraphrase.

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

   **Mandatory post-write integrity check (deep mode only).** After writing the raw file, re-read it and verify:
   - Contains a `## Discovery audit` section with non-empty candidate lists. **If absent, the discovery sanity check (step 5d) was skipped — abort the ingest with the error: "Discovery audit missing in raw file `<path>` — Step 5 sanity check was skipped or output was lost. Re-run after fixing the discovery flow." Do not proceed to ingest. Surface the error to the user.**
   - Contains a `## llms.txt — <url>` section (if llms.txt was non-empty in step 2) whose body is the verbatim curl output. Spot-check by computing `wc -l` of the section body vs `wc -l` of `/tmp/pin-llm-wiki-llmstxt-<slug>.txt`; if the section is significantly shorter (e.g. <50% of the line count), it was summarized — abort with: "llms.txt section in `<path>` is paraphrased, not verbatim. Re-fetch and paste the curl output literally."
   - In `deep-multi-product` mode: `Products discovered: N` in the fetch log equals the number of `## Product:` sections in the body. If they disagree, abort with a structural-mismatch error.

   These checks are load-bearing. They convert step 5d ("write the audit") from an instruction the agent can ignore into a hard precondition for ingest. A skipped check fails the run loudly.
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

## llms.txt — <https://<domain>/llms.txt>     ← present if curl returned a non-empty catalog response
<verbatim curl response — every line, every section heading, every URL — DO NOT summarize, DO NOT list "relevant entries"; the curl bytes go here>

## Discovery audit     ← present at deep mode only; written from Step 5d
- Candidates from llms.txt (depth 1/2/3): <list>
- Candidates from landing page: <list>
- Candidates from sitemap.xml: <list>
- Candidates from GitHub URLs: <list>
- Classified as products: <list>
- Classified as excluded: <list — and why>
- Classified as sub-section of existing product: <list — and which parent>

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
