"""Print the RSA modulus from Primeval metadata."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Optional


DATA_DIR = Path("data")
DEFAULT_METADATA_PATH = DATA_DIR / "metadata.json"


def read_modulus(metadata: Path = DEFAULT_METADATA_PATH) -> int:
    md = json.loads(metadata.read_text())
    return int(md["n"])


def build_parser(prog: str = "primeval modulus") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Print the RSA modulus n from metadata.json.",
    )
    parser.add_argument(
        "-m",
        "--metadata",
        type=Path,
        default=DEFAULT_METADATA_PATH,
        help=f"metadata input path (default: {DEFAULT_METADATA_PATH})",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    try:
        print(read_modulus(args.metadata))
    except Exception as exc:
        print("Failed to read modulus:", exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
