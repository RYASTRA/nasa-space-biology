"""Observatory status contract (schema 1) for this site.

Emits the small, stable status.json the NASA Observatory reads from every
fleet site's root. Contract spec:
https://github.com/RYASTRA/nasa-observatory/blob/main/docs/superpowers/specs/2026-07-22-nasa-observatory-design.md

Display strings are decided HERE — the Observatory renders them verbatim.
Bounds: headline <= 120 chars, <= 5 items, item text <= 140 chars.
updated_utc is the SNAPSHOT's generated_at, not build time: a push-triggered
redeploy rebuilds this file without refreshing data and must not look fresh.
"""

from __future__ import annotations

from typing import Any

from .site import newest_by_release

_SITE_URL = "https://ryastra.github.io/nasa-space-biology/"


def build(meta: dict[str, Any], studies: list[dict[str, Any]]) -> dict[str, Any]:
    """The status.json document, from the same mirror build_site renders."""
    newest = newest_by_release(studies, limit=5)
    count = meta["study_count"]
    if newest:
        first = newest[0]
        headline = (
            f"{count} open studies — newest {first['identity']['accession']} "
            f"({first['overview']['release_date']})"
        )
    else:
        headline = f"{count} open studies"
    return {
        "schema": 1,
        "project": "nasa-space-biology",
        "title": "OSDR Space-Biology Explorer",
        "site": _SITE_URL,
        "updated_utc": meta["generated_at"].replace("+00:00", "Z"),
        "fresh_for_hours": 192,
        # the weekly snapshot job fails the whole build on collection errors,
        # so a freshly built status.json implies the collection succeeded
        "ok": True,
        "headline": headline[:120],
        "metrics": [
            {"label": "Open studies", "value": str(count)},
            {
                "label": "Newest release",
                "value": newest[0]["overview"]["release_date"] if newest else "—",
            },
        ],
        "items": [
            {
                "when_utc": s["overview"]["release_date"],
                "text": f"{s['identity']['accession']} — {s['overview']['title']}"[:140],
                "url": s["identity"]["links"]["study"],
            }
            for s in newest
        ],
    }
