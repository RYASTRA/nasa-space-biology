# Security Policy

## Supported Versions

`nasa-space-biology` is a continuously-deployed static site, not a released library.
There is one running instance — the scheduled GitHub Actions workflow on `main` that
snapshots OSDR and publishes the explorer to GitHub Pages. Fixes land on `main`; there
are no maintained release branches or version tags.

| Ref                        | Supported          |
| -------------------------- | ------------------ |
| `main` (deployed)          | :white_check_mark: |
| forks / older commits      | :x:                |

## Reporting a Vulnerability

Please report security issues **privately** — do not open a public Issue. The watcher
auto-generates world-readable Issues in this repo, so a report filed there is immediately
public.

Use GitHub's [private vulnerability reporting][report] ("Report a vulnerability" under the
**Security** tab). Expect an initial acknowledgement within a week; this is a personal
project maintained on a best-effort basis, so please allow time for a fix before any
public disclosure.

[report]: https://github.com/RYASTRA/nasa-space-biology/security/advisories/new

## Security model

What is and isn't security-relevant in this project:

- **No user data, no backend.** The deployed site is pure static files (committed JSON +
  HTML/CSS/JS) served by GitHub Pages — no server, database, login, or form. It collects
  nothing from visitors.
- **Keyless source → zero client-side secrets.** The OSDR API is public and keyless, so
  the browser only ever loads committed static JSON; there is nothing to leak client-side,
  and no API key is involved in fetching OSDR data.
- **Secrets (build-time only).** CI reads `GITHUB_TOKEN` (to commit the weekly snapshot,
  open the new-study digest Issue, and deploy Pages) and `GITLAB_TOKEN` (used solely by
  the mirror workflow to push to GitLab). Both come from GitHub Actions secrets; a local
  `.env` is gitignored and never committed. No secret is written to committed state, run
  logs, or the published site.
- **Token scope & least privilege.** Every workflow declares an explicit least-privilege
  `permissions:` block, and the default `GITHUB_TOKEN` is scoped to this repository only —
  no organization-wide or cross-repository access.
- **Outbound traffic.** The snapshot job makes outbound HTTPS requests only to the keyless
  OSDR API (`osdr.nasa.gov`). The published pages load only committed assets plus
  OSDR-hosted study thumbnails; the site accepts no inbound network input.
- **Dependencies.** The runtime surface is intentionally minimal — `httpx` and `jinja2`,
  plus a vendored, version-pinned copy of MiniSearch for client-side search — and is
  tracked by GitHub's dependency graph.
