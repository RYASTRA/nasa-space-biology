"""Command-line entry point for the OSDR explorer."""

import argparse


def main(argv: list[str] | None = None) -> int:
    """Parse arguments and dispatch to a subcommand. Returns a process exit code."""
    parser = argparse.ArgumentParser(prog="osdr_explorer")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("snapshot", help="Fetch OSDR studies and write the JSON mirror.")
    parser.parse_args(argv)
    return 0
