### GitHub fetch protocol

**Trigger:** inbox URL matches `github.com/<org>/<repo>`.
**Tool:** `gh` CLI.

Steps:

1. `gh repo view <org>/<repo> --json name,description,url,homepageUrl,stargazerCount,forkCount,pushedAt,primaryLanguage,licenseInfo,defaultBranchRef` — capture metadata and default branch name.
2. `gh release list --repo <org>/<repo> --limit 1` — capture latest release tag.
3. `gh api repos/<org>/<repo>/readme` — base64-decode and capture full README.
4. `gh api repos/<org>/<repo>/contents/` — top-level structure listing.
5. If `docs/` exists: list contents + fetch key files (guides, architecture, testing, overview).
6. If `examples/` exists: list structure only (do not fetch full example files unless `deep`).
7. Skim other top-level folders; annotate important ones (source/lib, plugin manifests, tests, agent instruction files `CLAUDE.md` / `AGENTS.md` / `GEMINI.md`); skip boilerplate (`.github/`, `node_modules/`, lock files).
8. Compile into a single file and save to `raw/github/<org>-<repo>.md`.
9. Use `defaultBranchRef.name` from step 1 as the branch. **Never assume `main`.** Override with `<!-- branch:X -->` inbox tag if present.
10. At `deep` detail with `<!-- clone -->` inbox tag: `git clone https://github.com/<org>/<repo>.git raw/github/<org>-<repo>/` (this path is gitignored; full clone tree for deep citation).

**Guard:** if the repo fetch would exceed 200k input tokens, halt and surface to the user before proceeding.

**Raw file format** (`raw/github/<org>-<repo>.md`):
```
# <org>/<repo>

## Metadata
- Stars: <N>
- Primary language: <lang>
- Default branch: <branch>
- Latest release: <tag> (<date>)
- License: <license>
- Homepage: <url>
- Fetched: <YYYY-MM-DD>
- Final URL: <url>

## Description
<description>

## README
<full readme content>

## Docs
<fetched doc files, one section each>

## Top-level structure
<annotated directory listing>
```

**README.md row format** (`raw/github/README.md`):
`| raw/github/<org>-<repo>.md | <org>/<repo> | <stars> | <default-branch> | <latest-release> | <YYYY-MM-DD> | |`
