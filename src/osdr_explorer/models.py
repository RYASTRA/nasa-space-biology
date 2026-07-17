"""Typed data models for OSDR studies, facets, and snapshot metadata."""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class StudyLinks:
    """Deep links from a study to its authoritative OSDR resources."""

    study: str
    metadata_api: str
    files_api: str


@dataclass(slots=True)
class Study:
    """A normalized OSDR study record, ready to serialize to the JSON mirror."""

    accession: str
    osd_num: int
    title: str
    description: str
    release_date: str | None
    identifiers: str
    organisms: list[str]
    assay_types: list[str]
    assay_measurement_types: list[str]
    assay_platforms: list[str]
    factor_names: list[str]
    factor_types: list[str]
    missions: list[str]
    flight_programs: list[str]
    space_programs: list[str]
    managing_center: str
    material_types: list[str]
    people: list[str]
    publication_title: str
    thumbnail: str | None
    links: StudyLinks

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict (nested ``links`` is expanded)."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FacetValue:
    """One value of a facet plus how many studies carry it."""

    value: str
    count: int


@dataclass(slots=True)
class SnapshotMeta:
    """Provenance for a snapshot run."""

    generated_at: str
    source: str
    study_count: int
    explorer_version: str
