"""Unified Primeval command line interface."""
from __future__ import annotations

import sys
from typing import Callable, Optional

from primeval import import_factors, modulus, parse, reconstruct


Command = Callable[[Optional[list[str]]], int]

COMMANDS: dict[str, tuple[str, Command]] = {
    "parse": ("extract n/e metadata from an OpenPGP public key", parse.main),
    "modulus": ("print n from metadata.json", modulus.main),
    "n": ("alias for modulus", modulus.main),
    "import-factors": ("extract p/q files from CADO-NFS output", import_factors.main),
    "reconstruct": ("build a PKCS#1 PEM private key", reconstruct.main),
    "recon": ("alias for reconstruct", reconstruct.main),
}


def print_help() -> None:
    print("usage: primeval <command> [options]")
    print()
    print("commands:")
    for name in ("parse", "modulus", "import-factors", "reconstruct"):
        print(f"  {name:<15} {COMMANDS[name][0]}")
    print()
    print("aliases: n -> modulus, recon -> reconstruct")
    print("run `primeval <command> --help` for command options")


def main(argv: Optional[list[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print_help()
        return 2

    command = argv[0]
    if command in ("-h", "--help"):
        print_help()
        return 0

    if command == "help":
        if len(argv) == 1:
            print_help()
            return 0
        command = argv[1]
        rest = ["--help"]
    else:
        rest = argv[1:]

    entry = COMMANDS.get(command)
    if entry is None:
        print(f"Unknown command: {command}", file=sys.stderr)
        print("Run `primeval --help` for available commands.", file=sys.stderr)
        return 2

    return entry[1](rest)


if __name__ == "__main__":
    raise SystemExit(main())
