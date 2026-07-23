# 🧬 nasa-space-biology — OSDR studies, findable

A **faceted explorer** for NASA's **Open Science Data Repository (OSDR)** — browse
space-biology studies by *organism × assay × exposure factor × mission*, with deep
links to study metadata and data files.

Pattern: **mirror + static explorer** (sibling of
[nasa-tech-explorer](https://github.com/RYASTRA/nasa-tech-explorer)). A periodic
GitHub Actions job snapshots OSDR study metadata into committed JSON; GitHub Pages
serves a client-side faceted search over it. The OSDR API is **keyless**, making
this the purest static build in the fleet — no servers, no secrets, no backend.

> **Status: ✅ live — 574 studies, refreshed weekly.**
> **Quick look:** <https://ryastra.github.io/nasa-space-biology/>

## The unmet need

OSDR holds the primary data of space biology — spaceflight and ground-analog
studies on organisms from microbes to mice to humans — but discovery through the
native interface is tedious. NASA funds OSDR to **maximize data reuse**; a humane
discovery layer directly serves that mandate, and the grad students doing the
reusing.

## What it does

1. **Periodic snapshot** — a weekly Actions job pulls OSDR study metadata (keyless
   API) into committed JSON.
2. **Faceted static explorer** — GitHub Pages site: filter by organism, assay
   type, exposure factor (microgravity, radiation, analogs), and mission/vehicle;
   full-text search across titles and descriptions; each study page deep-links to
   its metadata and files via the OSDR API.
3. **New-study watcher** — a weekly diff of the snapshot opens a GitHub Issue and
   updates an Atom feed of new & updated studies.

## Audiences

- **Space-biology researchers & space-medicine grad students** — find reusable
  datasets in seconds instead of sessions
- **Biologists curious about spaceflight effects** — a browsable map of what's
  been studied, in plain terms

## Data source

NASA **OSDR** public API (study search, metadata, and file listings) — **keyless**.

## The RYASTRA fleet

| Repo | What it is |
|---|---|
| [nasa-defense](https://github.com/RYASTRA/nasa-defense) | Planetary-defense watch (the original watcher engine) |
| [nasa-mcp](https://github.com/RYASTRA/nasa-mcp) | All 16 NASA public APIs as an MCP server (R&D layer) |
| [nasa-new-worlds](https://github.com/RYASTRA/nasa-new-worlds) | New-worlds watch — exoplanet confirmations |
| [nasa-observatory](https://github.com/RYASTRA/nasa-observatory) | Fleet dashboard — one tile per watcher |
| **nasa-space-biology** | Faceted explorer for OSDR space-biology studies *(this repo)* |
| [nasa-space-weather](https://github.com/RYASTRA/nasa-space-weather) | Space-weather watch |
| [nasa-tech-explorer](https://github.com/RYASTRA/nasa-tech-explorer) | NASA patents, free software & spinoffs — searchable |

## License

[MIT](LICENSE)
