"""Tests for the Observatory status.json contract (schema 1)."""

from __future__ import annotations

import json
from pathlib import Path

from osdr_explorer import status


def _study(osd_num: int, release_date: str | None, title: str = "Study") -> dict:
    accession = f"OSD-{osd_num}"
    return {
        "identity": {
            "accession": accession,
            "osd_num": osd_num,
            "links": {"study": f"https://osdr.nasa.gov/bio/repo/data/studies/{accession}"},
        },
        "overview": {"title": title, "release_date": release_date},
    }


def _meta() -> dict:
    return {"generated_at": "2026-07-18T02:49:00Z", "study_count": 3}


def test_contract_envelope_ordering_and_undated_exclusion() -> None:
    studies = [
        _study(1, "2020-01-01"),
        _study(955, "2025-12-08", title="Newest study"),
        _study(500, None),  # undated: excluded, exactly as the Atom feed excludes it
        _study(600, "2024-06-15"),
    ]
    doc = status.build(_meta(), studies)

    assert doc["schema"] == 1
    assert doc["project"] == "nasa-space-biology"
    assert doc["site"] == "https://ryastra.github.io/nasa-space-biology/"
    assert doc["fresh_for_hours"] == 192
    assert doc["ok"] is True
    assert doc["updated_utc"] == "2026-07-18T02:49:00Z"
    assert doc["headline"] == "3 open studies — newest OSD-955 (2025-12-08)"
    assert len(doc["headline"]) <= 120
    assert 1 <= len(doc["metrics"]) <= 4

    assert [i["when_utc"] for i in doc["items"]] == ["2025-12-08", "2024-06-15", "2020-01-01"]
    assert doc["items"][0]["text"] == "OSD-955 — Newest study"
    assert doc["items"][0]["url"] == "https://osdr.nasa.gov/bio/repo/data/studies/OSD-955"
    assert all(len(i["text"]) <= 140 for i in doc["items"])
    assert len(doc["items"]) <= 5


def test_long_titles_are_truncated_with_ellipsis_and_lists_capped() -> None:
    studies = [_study(n, f"2025-01-{n:02d}", title="T" * 300) for n in range(1, 9)]
    doc = status.build({"generated_at": "2026-07-18T02:49:00Z", "study_count": 8}, studies)
    assert len(doc["items"]) == 5
    assert all(len(i["text"]) <= 140 for i in doc["items"])
    assert all(i["text"].endswith("…") for i in doc["items"])


def test_status_json_is_valid_json_when_dumped(tmp_path: Path) -> None:
    doc = status.build(_meta(), [_study(1, "2020-01-01")])
    path = tmp_path / "status.json"
    path.write_text(json.dumps(doc, indent=1), encoding="utf-8")
    assert json.loads(path.read_text(encoding="utf-8"))["project"] == "nasa-space-biology"
