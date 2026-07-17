"""Pure functions that turn dirty OSDR search records into clean values."""

import re
from datetime import datetime, timezone

from osdr_explorer import OSDR_HOST
from osdr_explorer.models import StudyLinks

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
    """Convert a Unix-epoch-seconds value (number or numeric string) to an ISO date."""
    if not isinstance(raw, (int, float, str)):
        return None
    if isinstance(raw, str) and not raw.strip():
        return None
    try:
        seconds = float(raw)
    except (TypeError, ValueError):
        return None
    return datetime.fromtimestamp(seconds, tz=timezone.utc).date().isoformat()


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
        str(person.get("First Name", "")).strip(),
        str(person.get("Middle Initials", "")).strip(),
        str(person.get("Last Name", "")).strip(),
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
