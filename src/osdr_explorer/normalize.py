"""Pure functions that turn dirty OSDR search records into clean values."""

import re
from datetime import datetime, timezone
from typing import Any

from osdr_explorer import OSDR_HOST
from osdr_explorer.models import (
    Assay,
    Attribution,
    Factors,
    Identity,
    Mission,
    Overview,
    Study,
    StudyLinks,
    Subject,
)

_SPLIT_RE = re.compile(r"\s{2,}|,")


def split_multi(raw: object) -> list[str]:
    """Split a multi-value OSDR string on commas or runs of 2+ spaces.

    Handles the two delimiters OSDR mixes (comma for organism, whitespace runs
    for factor fields), strips each token, and drops empty tokens (e.g. the
    leading comma in the real value ``", Bacillus"``).
    """
    if not isinstance(raw, str):
        return []
    return [token.strip() for token in _SPLIT_RE.split(raw) if token.strip()]


def parse_epoch_date(raw: object) -> str | None:
    """Convert a Unix-epoch-seconds value (number or numeric string) to an ISO date.

    Returns ``None`` for anything that is not a finite, in-range epoch — non-numeric,
    empty, NaN, infinite, or outside ``datetime``'s year range — so one malformed
    release date can never abort an unattended snapshot run.
    """
    if not isinstance(raw, (int, float, str)):
        return None
    if isinstance(raw, str) and not raw.strip():
        return None
    try:
        seconds = float(raw)
        return datetime.fromtimestamp(seconds, tz=timezone.utc).date().isoformat()
    except (ValueError, OverflowError, OSError):
        return None


def osd_num_from_accession(accession: str) -> int:
    """Return the numeric id from an accession, e.g. ``"OSD-379"`` -> ``379``."""
    return int(accession.split("-", 1)[1])


def build_links(accession: str) -> StudyLinks:
    """Build the three OSDR deep links for a study accession."""
    num = osd_num_from_accession(accession)
    return StudyLinks(
        study=f"{OSDR_HOST}/bio/repo/data/studies/{accession}",
        metadata_api=f"{OSDR_HOST}/osdr/data/osd/meta/{num}",
        files_api=f"{OSDR_HOST}/osdr/data/osd/files/{num}",
    )


def normalize_thumbnail(raw: object) -> str | None:
    """Return an absolute thumbnail URL, prefixing OSDR host for relative paths."""
    if not isinstance(raw, str) or not raw.strip():
        return None
    value = raw.strip()
    if value.startswith(("http://", "https://")):
        return value
    if value.startswith("/"):
        return f"{OSDR_HOST}{value}"
    return value


def _person_name(person: object) -> str:
    """Join a person dict's name parts into a single trimmed string."""
    if not isinstance(person, dict):
        return ""
    parts = [
        str(person.get("First Name") or "").strip(),
        str(person.get("Middle Initials") or "").strip(),
        str(person.get("Last Name") or "").strip(),
    ]
    return " ".join(part for part in parts if part)


def normalize_people(raw: object) -> list[str]:
    """Normalize the ``Study Person`` field (dict or list of dicts) to names."""
    if isinstance(raw, dict):
        name = _person_name(raw)
        return [name] if name else []
    if isinstance(raw, list):
        names = [_person_name(person) for person in raw]
        return [name for name in names if name]
    return []


class NormalizeError(Exception):
    """Raised when an OSDR record cannot be normalized (e.g. missing accession)."""


def _mission_name(raw: object) -> list[str]:
    """Extract a single-element mission-name list from the Mission object."""
    if isinstance(raw, dict):
        name = str(raw.get("Name") or "").strip()
        return [name] if name else []
    return []


def normalize_record(raw: dict[str, Any]) -> Study:
    """Convert one raw OSDR search record into a typed :class:`Study`.

    Raises :class:`NormalizeError` if the record has no usable ``Accession``.
    """
    accession = str(raw.get("Accession") or "").strip()
    if not accession or "-" not in accession:
        raise NormalizeError(f"record has no usable Accession: {raw.get('Accession')!r}")
    try:
        osd_num = osd_num_from_accession(accession)
    except ValueError as exc:
        raise NormalizeError(f"malformed Accession (non-numeric id): {accession!r}") from exc
    return Study(
        identity=Identity(
            accession=accession,
            osd_num=osd_num,
            identifiers=str(raw.get("Identifiers") or "").strip(),
            links=build_links(accession),
        ),
        overview=Overview(
            title=str(raw.get("Study Title") or "").strip(),
            description=str(raw.get("Study Description") or "").strip(),
            release_date=parse_epoch_date(raw.get("Study Public Release Date")),
            thumbnail=normalize_thumbnail(raw.get("thumbnail")),
        ),
        subject=Subject(
            organisms=split_multi(raw.get("organism")),
            material_types=split_multi(raw.get("Material Type")),
        ),
        assay=Assay(
            types=split_multi(raw.get("Study Assay Technology Type")),
            measurement_types=split_multi(raw.get("Study Assay Measurement Type")),
            platforms=split_multi(raw.get("Study Assay Technology Platform")),
        ),
        factors=Factors(
            names=split_multi(raw.get("Study Factor Name")),
            types=split_multi(raw.get("Study Factor Type")),
        ),
        mission=Mission(
            names=_mission_name(raw.get("Mission")),
            flight_programs=split_multi(raw.get("Flight Program")),
            space_programs=split_multi(raw.get("Space Program")),
        ),
        attribution=Attribution(
            managing_center=str(raw.get("Managing NASA Center") or "").strip(),
            people=normalize_people(raw.get("Study Person")),
            publication_title=str(raw.get("Study Publication Title") or "").strip(),
        ),
    )
