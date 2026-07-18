"""Watcher: diff the new mirror against the previous committed one (new + updated)."""

from dataclasses import dataclass
from typing import Any


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
