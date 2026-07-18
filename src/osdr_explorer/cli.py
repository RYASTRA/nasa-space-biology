"""Command-line entry point for the OSDR explorer."""

import argparse
import logging
from pathlib import Path

import httpx

from osdr_explorer import __version__
from osdr_explorer.api import SNAPSHOT_SOURCE, OSDRClient, build_client
from osdr_explorer.site import build_site
from osdr_explorer.snapshot import (
    build_snapshot,
    check_sanity_floor,
    read_previous_count,
    write_snapshot,
)

logger = logging.getLogger(__name__)


def run_snapshot(*, data_dir: Path, client: httpx.Client | None = None) -> int:
    """Fetch OSDR studies and write the JSON mirror into data_dir. Returns an exit code."""
    owns_client = client is None
    active = client or build_client()
    try:
        records = OSDRClient(active).fetch_all_studies()
    finally:
        if owns_client:
            active.close()

    studies, facets, meta = build_snapshot(records, source=SNAPSHOT_SOURCE, version=__version__)
    check_sanity_floor(meta.study_count, read_previous_count(data_dir))
    write_snapshot(data_dir, studies, facets, meta)
    logger.info("wrote %d studies to %s", meta.study_count, data_dir)
    return 0


def run_build(*, data_dir: Path, site_dir: Path) -> int:
    """Render the static site into site_dir from the mirror in data_dir. Returns an exit code."""
    build_site(
        data_dir=data_dir,
        site_dir=site_dir,
        templates_dir=Path("templates"),
        assets_dir=Path("assets"),
    )
    logger.info("built site at %s", site_dir)
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to a subcommand. Returns a process exit code."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(prog="osdr_explorer")
    subparsers = parser.add_subparsers(dest="command", required=True)
    snap = subparsers.add_parser("snapshot", help="Fetch OSDR studies and write the JSON mirror.")
    snap.add_argument("--data-dir", type=Path, default=Path("data"), help="Output directory.")
    build = subparsers.add_parser("build", help="Render the static explorer site from the mirror.")
    build.add_argument("--data-dir", type=Path, default=Path("data"), help="Mirror directory.")
    build.add_argument("--site-dir", type=Path, default=Path("site"), help="Output site directory.")
    args = parser.parse_args(argv)
    if args.command == "snapshot":
        return run_snapshot(data_dir=args.data_dir)
    if args.command == "build":
        return run_build(data_dir=args.data_dir, site_dir=args.site_dir)
    return 1
