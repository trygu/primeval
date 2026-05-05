from pathlib import Path

import pgpy


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

        # Simulate recovered factors from CADO output
        pkt = key._key
        km = getattr(pkt, "keymaterial", pkt)
        p = int(getattr(km, "p"))
        q = int(getattr(km, "q"))

        # Write factors directly from simulated CADO output
        (tmp_path / "data" / "p.txt").write_text(str(p))
        (tmp_path / "data" / "q.txt").write_text(str(q))

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
