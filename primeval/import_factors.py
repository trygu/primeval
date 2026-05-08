"""Extract p and q factor files from CADO-NFS output."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Optional


DATA_DIR = Path("data")
DEFAULT_SOURCE_PATH = DATA_DIR / "factors.txt"
DEFAULT_METADATA_PATH = DATA_DIR / "metadata.json"
DEFAULT_P_PATH = DATA_DIR / "p.txt"
DEFAULT_Q_PATH = DATA_DIR / "q.txt"

INTEGER_RE = re.compile(r"\d+")


def read_expected_n(metadata: Path = DEFAULT_METADATA_PATH) -> Optional[int]:
    if not metadata.exists():
        return None
    md = json.loads(metadata.read_text())
    return int(md["n"])


def _integers_from_bottom(text: str) -> list[int]:
    values: list[int] = []
    for line in reversed(text.splitlines()):
        values.extend(int(value) for value in reversed(INTEGER_RE.findall(line)))
    return values


def find_factors(text: str, expected_n: Optional[int] = None) -> tuple[int, int]:
    if expected_n is not None:
        seen: set[int] = set()
        for value in _integers_from_bottom(text):
            if value > 1 and expected_n % value == 0:
                other = expected_n // value
                if other in seen:
                    return value, other
            seen.add(value)
        raise ValueError("Could not find factors that multiply to metadata n")

    for line in reversed(text.splitlines()):
        values = [int(value) for value in INTEGER_RE.findall(line)]
        if len(values) == 2:
            return values[0], values[1]

    raise ValueError("Could not find a line containing exactly two integers")


def write_factors(
    p: int,
    q: int,
    p_path: Path = DEFAULT_P_PATH,
    q_path: Path = DEFAULT_Q_PATH,
) -> tuple[Path, Path]:
    p_path.parent.mkdir(parents=True, exist_ok=True)
    q_path.parent.mkdir(parents=True, exist_ok=True)
    p_path.write_text(str(p))
    q_path.write_text(str(q))
    return p_path, q_path


def build_parser(prog: str = "primeval import-factors") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Extract p and q from CADO-NFS output and write factor files.",
    )
    parser.add_argument(
        "source",
        metavar="SOURCE",
        nargs="?",
        type=Path,
        default=DEFAULT_SOURCE_PATH,
        help=f"CADO-NFS output path (default: {DEFAULT_SOURCE_PATH})",
    )
    parser.add_argument(
        "-m",
        "--metadata",
        type=Path,
        default=DEFAULT_METADATA_PATH,
        help=f"metadata path used to validate factors (default: {DEFAULT_METADATA_PATH})",
    )
    parser.add_argument(
        "-p",
        "--p",
        dest="p_path",
        type=Path,
        default=DEFAULT_P_PATH,
        help=f"p factor output path (default: {DEFAULT_P_PATH})",
    )
    parser.add_argument(
        "-q",
        "--q",
        dest="q_path",
        type=Path,
        default=DEFAULT_Q_PATH,
        help=f"q factor output path (default: {DEFAULT_Q_PATH})",
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

    if not args.source.exists():
        print("Factor output not found:", args.source, file=sys.stderr)
        return 2

    try:
        expected_n = read_expected_n(args.metadata)
    except Exception as exc:
        print("Failed to read metadata:", exc, file=sys.stderr)
        return 3

    try:
        p, q = find_factors(args.source.read_text(), expected_n)
    except Exception as exc:
        print("Failed to extract factors:", exc, file=sys.stderr)
        return 4

    p_path, q_path = write_factors(p, q, args.p_path, args.q_path)
    print("Wrote", p_path, "and", q_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
