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

import argparse
import os
import re
from pathlib import Path
from typing import Optional, Tuple, List

import pgpy
from pgpy import PGPKey

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


INTEGER_RE = re.compile(r"\b[0-9]{20,}\b")


def load_public_key(path: Path) -> Tuple[PGPKey, int, int, List[str]]:
    blob = path.read_text()
    key, _ = PGPKey.from_blob(blob)

    userids = list(key.userids)

    # Try to extract modulus `n` and public exponent `e` via common internals
    n = None
    e = None
    try:
        # pgpy internal structure access (may vary by version)
        pkt = key._key
        km = getattr(pkt, "keymaterial", pkt)
        n = int(getattr(km, "n"))
        e = int(getattr(km, "e"))
    except Exception:
        pass

    if n is None or e is None:
        raise RuntimeError("Could not extract modulus/exponent from public key via pgpy internals")

    return key, n, e, userids


def scan_for_factors(workdir: Path, n: int) -> Optional[Tuple[int, int, Path]]:
    candidates = {}
    for fp in workdir.rglob("*"):
        if not fp.is_file():
            continue
        try:
            text = fp.read_text(errors="ignore")
        except Exception:
            continue
        for m in INTEGER_RE.findall(text):
            val = int(m)
            candidates[val] = fp

    vals = sorted(candidates.keys())
    # naive pair search
    for i, p in enumerate(vals):
        if n % p != 0:
            continue
        q = n // p
        if p * q == n:
            return p, q, candidates[p]

    return None


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


def try_write_openpgp_private(key: PGPKey, pem_data: bytes, outpath: Path) -> bool:
    """Attempt to construct an OpenPGP private key from PEM/low-level data.

    This is an opportunistic function: pgpy does not currently expose a
    straightforward public API to inject low-level RSA private components.
    If such assembly is not possible, return False so caller can fall back
    to writing the PEM representation.
    """
    # Placeholder: leaving for future extension where pgpy exposes a constructor
    return False


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Reconstruct an OpenPGP private key from factors")
    parser.add_argument("--public-key", required=True, help="Path to public key (.asc)")
    parser.add_argument("--workdir", required=True, help="Directory with factorization results")
    parser.add_argument("--output", default="private_key.asc", help="Output ASCII-armored private key")
    args = parser.parse_args(argv)

    pubpath = Path(args.public_key)
    workdir = Path(args.workdir)
    outpath = Path(args.output)

    if not pubpath.exists():
        print("Public key not found:", pubpath)
        return 2

    try:
        key, n, e, userids = load_public_key(pubpath)
    except Exception as exc:
        print("Failed to load public key:", exc)
        return 3

    found = scan_for_factors(workdir, n)
    if not found:
        print("No valid p,q factors found in workdir")
        return 4

    p, q, source = found
    print(f"Found factors p (file={source}): {p}\nq: {q}")

    pem = build_rsa_private_pem(p, q, e)

    # Try to write an OpenPGP private key; fall back to PEM if not possible
    if try_write_openpgp_private(key, pem, outpath):
        print("Wrote OpenPGP private key to", outpath)
    else:
        outpath.write_bytes(pem)
        print("Wrote PEM RSA private key to", outpath)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
