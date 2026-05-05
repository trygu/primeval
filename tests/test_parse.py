"""Tests for parse.py - PGP key modulus extraction."""
import json
import os
from pathlib import Path

import pgpy
import pytest

from primeval.parse import extract, main as parse_main

PUBKEY_ASC = Path(__file__).parent.parent / "primeval" / "publickey.asc"


def test_extract_v4_key():
    """extract() works on a freshly generated pgpy v4 key."""
    key = pgpy.PGPKey.new(pgpy.constants.PubKeyAlgorithm.RSAEncryptOrSign, 1024)
    uid = pgpy.PGPUID.new("Test", email="t@example.com")
    key.add_uid(
        uid,
        usage={pgpy.constants.KeyFlags.Sign},
        hashes=[pgpy.constants.HashAlgorithm.SHA256],
        ciphers=[pgpy.constants.SymmetricKeyAlgorithm.AES256],
        compression=[pgpy.constants.CompressionAlgorithm.ZLIB],
    )
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".asc", mode="w", delete=False) as f:
        f.write(str(key.pubkey))
        fname = f.name
    try:
        md = extract(Path(fname))
        assert "n" in md
        assert "e" in md
        n = int(md["n"])
        assert n > 0
        assert n.bit_length() == 1024
    finally:
        os.unlink(fname)


def test_extract_real_v2_key():
    """extract() can parse the actual v2/v3 publickey.asc used in this project."""
    if not PUBKEY_ASC.exists():
        pytest.skip("publickey.asc not present")
    md = extract(PUBKEY_ASC)
    n = int(md["n"])
    assert n.bit_length() >= 500, "Expected a large RSA modulus"
    assert int(md.get("e", 0)) > 0


def test_parse_main_writes_files(tmp_path):
    """parse main() writes metadata.json."""
    if not PUBKEY_ASC.exists():
        pytest.skip("publickey.asc not present")
    oldcwd = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        rv = parse_main([str(PUBKEY_ASC)])
        assert rv == 0
        md = json.loads((tmp_path / "data" / "metadata.json").read_text())
        assert int(md["n"]) > 0
    finally:
        os.chdir(oldcwd)
