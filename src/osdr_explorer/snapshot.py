"""Orchestrate normalization into the committed JSON mirror."""

import json
import logging
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from osdr_explorer.models import FacetValue, SnapshotMeta, Study
from osdr_explorer.normalize import NormalizeError, normalize_record

logger = logging.getLogger(__name__)


class SanityFloorError(Exception):
    """Raised when a new snapshot's study count is implausibly small."""


def _facet_values(study: Study) -> dict[str, list[str]]:
    """Map each facet name to this study's values (explicit, so pyright stays clean)."""
    return {
        "organisms": study.subject.organisms,
        "assay_types": study.assay.types,
        "factor_types": study.factors.types,
        "flight_programs": study.mission.flight_programs,
    }


def build_facets(studies: list[Study]) -> dict[str, list[FacetValue]]:
    """Count facet values across all studies, sorted by count desc then value asc."""
    counters: dict[str, Counter[str]] = {
        "organisms": Counter(),
        "assay_types": Counter(),
        "factor_types": Counter(),
        "flight_programs": Counter(),
    }
    for study in studies:
        for name, values in _facet_values(study).items():
            counters[name].update(set(values))
    return {
        name: [
            FacetValue(value=value, count=count)
            for value, count in sorted(counter.items(), key=lambda kv: (-kv[1], kv[0]))
        ]
        for name, counter in counters.items()
    }


def build_snapshot(
    records: list[dict[str, Any]],
    *,
    source: str,
    version: str,
    generated_at: str | None = None,
) -> tuple[list[Study], dict[str, list[FacetValue]], SnapshotMeta]:
    """Normalize records (skipping malformed ones), build facets, and assemble metadata."""
    studies: list[Study] = []
    for raw in records:
        try:
            studies.append(normalize_record(raw))
        except NormalizeError as error:
            logger.warning("skipping malformed record: %s", error)
    studies.sort(key=lambda s: s.identity.osd_num)
    facets = build_facets(studies)
    stamp = generated_at or datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    meta = SnapshotMeta(
        generated_at=stamp, source=source, study_count=len(studies), explorer_version=version
    )
    return studies, facets, meta


def read_previous_count(data_dir: Path) -> int | None:
    """Return the study_count from an existing meta.json, or None if absent/unreadable."""
    meta_path = data_dir / "meta.json"
    if not meta_path.exists():
        return None
    try:
        data: dict[str, Any] = json.loads(meta_path.read_text(encoding="utf-8"))
        return int(data["study_count"])
    except (ValueError, TypeError, KeyError, OSError):
        return None


def check_sanity_floor(
    new_count: int, previous_count: int | None, *, floor_ratio: float = 0.9
) -> None:
    """Raise SanityFloorError if the corpus shrank below floor_ratio of the last run."""
    if previous_count is not None and new_count < previous_count * floor_ratio:
        raise SanityFloorError(
            f"study count {new_count} is below {floor_ratio:.0%} of previous {previous_count}"
        )


def _write_json(path: Path, payload: object) -> None:
    """Write payload as pretty, deterministic JSON with a trailing newline."""
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    path.write_text(text + "\n", encoding="utf-8")


def write_snapshot(
    data_dir: Path,
    studies: list[Study],
    facets: dict[str, list[FacetValue]],
    meta: SnapshotMeta,
) -> None:
    """Write studies.json, facets.json, and meta.json into data_dir."""
    data_dir.mkdir(parents=True, exist_ok=True)
    _write_json(data_dir / "studies.json", [study.to_dict() for study in studies])
    _write_json(
        data_dir / "facets.json",
        {name: [asdict(fv) for fv in values] for name, values in facets.items()},
    )
    _write_json(data_dir / "meta.json", asdict(meta))
