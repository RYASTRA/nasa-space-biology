"""Watcher: diff the new mirror against the previous committed one (new + updated)."""

import json
import logging
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment

from osdr_explorer.site import DEFAULT_BASE_URL, make_env

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Changes:
    """New and updated study accessions found between two mirrors."""

    new: list[str]
    updated: list[str]


def _by_accession(studies: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Index a study list by accession."""
    return {s["identity"]["accession"]: s for s in studies}


def compute_changes(old: list[dict[str, Any]], new: list[dict[str, Any]]) -> Changes:
    """Return newly-added and substantively-updated accessions (sorted).

    New = accession absent from ``old``. Updated = accession in both whose full
    normalized record differs. Removed accessions are ignored.
    """
    old_map = _by_accession(old)
    new_map = _by_accession(new)
    new_acc = sorted(a for a in new_map if a not in old_map)
    updated_acc = sorted(a for a in new_map if a in old_map and new_map[a] != old_map[a])
    return Changes(new=new_acc, updated=updated_acc)


@dataclass(frozen=True, slots=True)
class _Unset:
    """Sentinel type for an unprovided ``previous`` override (distinct from None)."""


_UNSET = _Unset()


@dataclass(frozen=True, slots=True)
class DigestOverrides:
    """Test-injectable overrides for values ``run_digest`` otherwise auto-detects.

    ``day`` overrides today's UTC date; ``previous`` overrides the git-read baseline
    (the committed ``HEAD:data/studies.json``). Production code leaves both at their
    defaults; tests inject explicit values for determinism and to avoid touching git.
    """

    day: str | None = None
    previous: list[dict[str, Any]] | None | _Unset = _UNSET


def read_previous_studies(
    rel_path: str = "data/studies.json", ref: str = "HEAD"
) -> list[dict[str, Any]] | None:
    """Read the committed studies.json at a git ref, or None if absent (first run)."""
    try:
        result = subprocess.run(
            ["git", "show", f"{ref}:{rel_path}"],
            capture_output=True,
            text=True,
            check=True,
        )
        data: list[dict[str, Any]] = json.loads(result.stdout)
        return data
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        return None


def render_digest(
    env: Environment,
    new_studies: list[dict[str, Any]],
    updated_studies: list[dict[str, Any]],
    day: str,
    base_url: str,
) -> str:
    """Render the dated markdown digest of new + updated studies."""
    template = env.get_template("digest.md.j2")
    return template.render(
        new=new_studies, updated=updated_studies, day=day, base_url=base_url.rstrip("/")
    )


def run_digest(
    *,
    data_dir: Path,
    digest_dir: Path,
    templates_dir: Path,
    base_url: str = DEFAULT_BASE_URL,
    overrides: DigestOverrides = DigestOverrides(),
) -> int:
    """Diff the working-tree mirror against the previous committed one; write a digest.

    Writes ``digest/{day}.md`` only when there are new/updated studies. First run
    (no baseline) seeds silently. ``overrides.previous`` is injectable for tests; when
    left unset it is read from ``HEAD`` via git. ``overrides.day`` defaults to today.
    """
    new_studies: list[dict[str, Any]] = json.loads(
        (data_dir / "studies.json").read_text(encoding="utf-8")
    )
    previous = overrides.previous
    old_studies: list[dict[str, Any]] | None = (
        read_previous_studies(f"{data_dir.name}/studies.json")
        if isinstance(previous, _Unset)
        else previous
    )
    if old_studies is None:
        logger.info("no committed baseline — first run, seeding silently")
        return 0
    changes = compute_changes(old_studies, new_studies)
    if not changes.new and not changes.updated:
        logger.info("no new or updated studies")
        return 0
    by_acc = _by_accession(new_studies)
    new_full = [by_acc[a] for a in changes.new]
    updated_full = [by_acc[a] for a in changes.updated]
    resolved_day = overrides.day or datetime.now(tz=timezone.utc).date().isoformat()
    env = make_env(templates_dir)
    text = render_digest(env, new_full, updated_full, resolved_day, base_url)
    digest_dir.mkdir(parents=True, exist_ok=True)
    (digest_dir / f"{resolved_day}.md").write_text(
        text if text.endswith("\n") else text + "\n", encoding="utf-8"
    )
    logger.info("wrote digest: %d new, %d updated", len(changes.new), len(changes.updated))
    return 0
