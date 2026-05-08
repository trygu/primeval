"""Build an RSA private key from metadata and recovered factors."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


DATA_DIR = Path("data")
DEFAULT_METADATA_PATH = DATA_DIR / "metadata.json"
DEFAULT_P_PATH = DATA_DIR / "p.txt"
DEFAULT_Q_PATH = DATA_DIR / "q.txt"
DEFAULT_OUTPUT_PATH = Path("private_key.asc")


def read_metadata(path: Path = DEFAULT_METADATA_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def read_factor(path: Path) -> int:
    if not path.exists():
        raise FileNotFoundError(path)
    return int(path.read_text().strip())


def build_rsa_private_pem(p: int, q: int, e: int) -> bytes:
    n = p * q
    phi = (p - 1) * (q - 1)
    d = pow(e, -1, phi)
    dp = d % (p - 1)
    dq = d % (q - 1)
    qinv = pow(q, -1, p)

    public_numbers = rsa.RSAPublicNumbers(e, n)
    private_numbers = rsa.RSAPrivateNumbers(p, q, d, dp, dq, qinv, public_numbers)
    private_key = private_numbers.private_key(default_backend())

    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    return pem


def write_private(key_pem: bytes, output: Path = DEFAULT_OUTPUT_PATH) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(key_pem)
    return output


def build_parser(prog: str = "primeval reconstruct") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Build a PKCS#1 PEM private key from metadata.json, p.txt, and q.txt.",
    )
    parser.add_argument(
        "-m",
        "--metadata",
        type=Path,
        default=DEFAULT_METADATA_PATH,
        help=f"metadata input path (default: {DEFAULT_METADATA_PATH})",
    )
    parser.add_argument(
        "-p",
        "--p",
        dest="p_path",
        type=Path,
        default=DEFAULT_P_PATH,
        help=f"p factor input path (default: {DEFAULT_P_PATH})",
    )
    parser.add_argument(
        "-q",
        "--q",
        dest="q_path",
        type=Path,
        default=DEFAULT_Q_PATH,
        help=f"q factor input path (default: {DEFAULT_Q_PATH})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help=f"private key output path (default: {DEFAULT_OUTPUT_PATH})",
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
        md = read_metadata(args.metadata)
        n = int(md.get("n"))
        e = int(md.get("e", 65537))
    except Exception as exc:
        print("Failed to read metadata:", exc, file=sys.stderr)
        return 2

    try:
        p = read_factor(args.p_path)
        q = read_factor(args.q_path)
    except Exception as exc:
        print("Missing factor files:", exc, file=sys.stderr)
        return 3

    if p * q != n:
        print("Factors do not multiply to n", file=sys.stderr)
        return 4

    pem = build_rsa_private_pem(p, q, e)
    out = write_private(pem, args.output)
    print("Wrote private key to", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
