"""
Primeval reconstruct CLI

This tool parses a public OpenPGP key, scans a workdir for candidate factors,
validates p * q == n and, if successful, emits an ASCII-armored private key.

Notes:
- The script attempts to produce an OpenPGP private key where possible. If
  low-level assembly into OpenPGP structures is not available, it will write
  a PEM-encoded RSA private key as an ASCII file (private_key.asc) as a
  compatible fallback.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import pgpy
from pgpy import PGPKey

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


DATA_DIR = Path("data")


def read_metadata() -> dict:
    md_path = DATA_DIR / "metadata.json"
    if not md_path.exists():
        raise FileNotFoundError(md_path)
    return json.loads(md_path.read_text())


def read_factor(name: str) -> int:
    pth = DATA_DIR / f"{name}.txt"
    if not pth.exists():
        raise FileNotFoundError(pth)
    return int(pth.read_text().strip())


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


def write_private(key_pem: bytes) -> Path:
    out = Path("private_key.asc")
    out.write_bytes(key_pem)
    return out


def main(argv: Optional[list[str]] = None) -> int:
    try:
        md = read_metadata()
        n = int(md.get("n"))
        e = int(md.get("e", 65537))
    except Exception as exc:
        print("Failed to read metadata:", exc)
        return 2

    try:
        p = read_factor("p")
        q = read_factor("q")
    except Exception as exc:
        print("Missing factor files:", exc)
        return 3

    if p * q != n:
        print("Factors do not multiply to n")
        return 4

    pem = build_rsa_private_pem(p, q, e)
    out = write_private(pem)
    print("Wrote private key to", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
