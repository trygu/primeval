"""Tests for reconstruct.py - private key assembly."""
import json
import os
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.serialization import load_pem_private_key

from primeval.reconstruct import build_rsa_private_pem, main as recon_main

# Small safe primes for fast tests
P = 961748941
Q = 982451653
E = 65537
N = P * Q


def test_build_rsa_private_pem_valid():
    """PEM output is a loadable RSA private key with correct modulus."""
    pem = build_rsa_private_pem(P, Q, E)
    key = load_pem_private_key(pem, password=None)
    pub = key.public_key()
    assert pub.public_numbers().n == N
    assert pub.public_numbers().e == E


def test_recon_main_success(tmp_path):
    """main() produces private_key.asc given correct p.txt / q.txt / metadata.json."""
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "p.txt").write_text(str(P))
    (tmp_path / "data" / "q.txt").write_text(str(Q))
    (tmp_path / "data" / "metadata.json").write_text(json.dumps({"n": N, "e": E}))

    oldcwd = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        rv = recon_main()
        assert rv == 0
        pem = (tmp_path / "private_key.asc").read_bytes()
        key = load_pem_private_key(pem, password=None)
        assert key.public_key().public_numbers().n == N
    finally:
        os.chdir(oldcwd)


def test_recon_main_wrong_factors(tmp_path):
    """main() returns non-zero when p * q != n."""
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "p.txt").write_text(str(P))
    (tmp_path / "data" / "q.txt").write_text(str(P))  # wrong: p*p != N
    (tmp_path / "data" / "metadata.json").write_text(json.dumps({"n": N, "e": E}))

    oldcwd = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        rv = recon_main()
        assert rv != 0
    finally:
        os.chdir(oldcwd)


def test_recon_main_missing_files(tmp_path):
    """main() returns non-zero when factor files are absent."""
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "metadata.json").write_text(json.dumps({"n": N, "e": E}))

    oldcwd = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        rv = recon_main()
        assert rv != 0
    finally:
        os.chdir(oldcwd)
