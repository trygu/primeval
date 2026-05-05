import tempfile
from pathlib import Path

import pgpy

from primeval.reconstruct import main as reconstruct_main


def test_full_pipeline(tmp_path: Path):
    # Step 0: generate ephemeral PGP key
    key = pgpy.PGPKey.new(pgpy.constants.PubKeyAlgorithm.RSAEncryptOrSign, 1024)
    uid = pgpy.PGPUID.new("Test User", email="test@example.com")
    key.add_uid(uid, usage={pgpy.constants.KeyFlags.Sign}, hashes=[pgpy.constants.HashAlgorithm.SHA256], ciphers=[pgpy.constants.SymmetricKeyAlgorithm.AES256], compression=[pgpy.constants.CompressionAlgorithm.ZLIB])

    pub_armored = str(key.pubkey)

    pubfile = tmp_path / "pub.asc"
    pubfile.write_text(pub_armored)

    # Run parse.py
    from primeval.parse import main as parse_main

    cwd = Path.cwd()
    try:
        # ensure the script writes to tmp_path/data
        (tmp_path / "data").mkdir()
        Path.cwd().chdir = False
    except Exception:
        pass

    # Use environment by changing into tmp_path for isolated data dir
    import os
    oldcwd = os.getcwd()
    os.chdir(str(tmp_path))
    try:
        rv = parse_main([str(pubfile)])
        assert rv == 0

        # Simulate CADO output: write a fake factorization.log with p and q
        pkt = key._key
        km = getattr(pkt, "keymaterial", pkt)
        p = int(getattr(km, "p"))
        q = int(getattr(km, "q"))

        log = tmp_path / "data" / "factorization.log"
        log.write_text(f"p = {p}\nq = {q}\n")

        # Run solve.py
        from primeval.solve import main as solve_main
        rv = solve_main([str(log)])
        assert rv == 0

        # Run reconstruct.py
        from primeval.reconstruct import main as recon_main
        rv = recon_main()
        assert rv == 0

        # Validate output
        out = tmp_path / "private_key.asc"
        assert out.exists()
        data = out.read_text()
        assert "BEGIN RSA" in data or "PRIVATE KEY" in data
    finally:
        os.chdir(oldcwd)
