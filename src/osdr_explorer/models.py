"""Typed data models for OSDR studies, facets, and snapshot metadata.

``Study`` groups its fields into small sub-records (identity, overview, subject,
assay, factors, mission, attribution). Each class stays a focused, flat data
record within pylint's default attribute budget — no suppressions, no threshold
overrides — and the grouping mirrors the OSDR domain (a study's identity vs.
biology vs. assay vs. mission context) rather than one wide bag of fields.
"""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class StudyLinks:
    """Deep links from a study to its authoritative OSDR resources."""

    study: str
    metadata_api: str
    files_api: str


@dataclass(frozen=True, slots=True)
class Identity:
    """A study's stable identifiers and its OSDR deep links."""

    accession: str
    osd_num: int
    identifiers: str
    links: StudyLinks


@dataclass(frozen=True, slots=True)
class Overview:
    """Human-facing summary of a study."""

    title: str
    description: str
    release_date: str | None
    thumbnail: str | None


@dataclass(frozen=True, slots=True)
class Subject:
    """What was studied: organisms and material types."""

    organisms: list[str]
    material_types: list[str]


@dataclass(frozen=True, slots=True)
class Assay:
    """How the study measured its subject."""

    types: list[str]
    measurement_types: list[str]
    platforms: list[str]


@dataclass(frozen=True, slots=True)
class Factors:
    """Experimental factors (exposure variables) under study."""

    names: list[str]
    types: list[str]


@dataclass(frozen=True, slots=True)
class Mission:
    """Spaceflight context: mission names and the programs behind them."""

    names: list[str]
    flight_programs: list[str]
    space_programs: list[str]


@dataclass(frozen=True, slots=True)
class Attribution:
    """Who ran the study and where it was published."""

    managing_center: str
    people: list[str]
    publication_title: str


@dataclass(frozen=True, slots=True)
class Study:
    """A normalized OSDR study record, ready to serialize to the JSON mirror."""

    identity: Identity
    overview: Overview
    subject: Subject
    assay: Assay
    factors: Factors
    mission: Mission
    attribution: Attribution

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dict (all nested sub-records expanded)."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FacetValue:
    """One value of a facet plus how many studies carry it."""

    value: str
    count: int


@dataclass(frozen=True, slots=True)
class SnapshotMeta:
    """Provenance for a snapshot run."""

    generated_at: str
    source: str
    study_count: int
    explorer_version: str
