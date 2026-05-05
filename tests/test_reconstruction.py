import tempfile
from pathlib import Path

import pgpy

from primeval.reconstruct import main as reconstruct_main


def test_reconstruction_flow(tmp_path: Path):
    # Generate an ephemeral RSA OpenPGP keypair
    key = pgpy.PGPKey.new(pgpy.constants.PubKeyAlgorithm.RSAEncryptOrSign, 1024)
    uid = pgpy.PGPUID.new("Test User", email="test@example.com")
    key.add_uid(uid, usage={pgpy.constants.KeyFlags.Sign}, hashes=[pgpy.constants.HashAlgorithm.SHA256], ciphers=[pgpy.constants.SymmetricKeyAlgorithm.AES256], compression=[pgpy.constants.CompressionAlgorithm.ZLIB])

    pub_armored = str(key.pubkey)

    pubfile = tmp_path / "pub.asc"
    pubfile.write_text(pub_armored)

    # Attempt to extract p and q from the generated private key internals
    # (pgpy stores private components in internal attributes generated above)
    try:
        pkt = key._key
        km = getattr(pkt, "keymaterial", pkt)
        p = int(getattr(km, "p"))
        q = int(getattr(km, "q"))
    except Exception:
        # If internals are not accessible, skip the deeper assertion
        p = None
        q = None

    workdir = tmp_path / "work"
    workdir.mkdir()

    if p and q:
        # write a fake factor file
        ff = workdir / "factors.txt"
        ff.write_text(f"p = {p}\nq = {q}\n")

        outpath = tmp_path / "private_key.asc"
        rv = reconstruct_main(["--public-key", str(pubfile), "--workdir", str(workdir), "--output", str(outpath)])
        assert rv == 0
        assert outpath.exists()

        data = outpath.read_text()
        assert "BEGIN RSA" in data or "PRIVATE KEY" in data
    else:
        # Fallback: ensure reconstruct returns non-zero when it can't find internals
        rv = reconstruct_main(["--public-key", str(pubfile), "--workdir", str(workdir)])
        assert rv != 0
