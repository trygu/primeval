# Primeval

Primeval is a prototype framework to reconstruct RSA/OpenPGP private keys by
matching metadata from a public key with discovered prime factors (p and q).

This repository contains two parts:

- A Python utility (`primeval.reconstruct`) that scans a workdir for factor
  files and reconstructs a private key when p and q for a public key's modulus
  are discovered.
- A Docker Compose setup to build and run CADO-NFS for factorization tasks
  (persistent `./data` and `./logs`).

WARNING: Reconstructed private keys are highly sensitive. Treat outputs with
extreme care (file permissions, encrypted storage, and secure deletion).

Quickstart
----------

1) Extract modulus from a public key (see `primeval.utils` helper).

2) Start the factorization environment (CADO-NFS) using Docker Compose. This
   will mount `./data` and `./logs` so factorization checkpoints persist.

```bash
docker compose up --build
```

3) When factors (`p` and `q`) appear in the `./data` output, run:

```bash
python -m primeval.reconstruct --public-key path/to/pub.asc --workdir ./data --output private_key.asc
```

This will attempt to assemble an OpenPGP private key. If low-level assembly
is not available in the installed `pgpy` version, the tool will write a PEM
encoded RSA private key as an ASCII file as a compatible fallback.

Development
-----------

Install dev dependencies with your preferred tool (the project is declared in
`pyproject.toml`). Run tests with `pytest`.

Files of interest:
- `primeval/reconstruct.py` - CLI and reconstruction logic
- `tests/test_reconstruction.py` - integration test (generates test key)
- `docker-compose.yml` - CADO-NFS service (builds from `./cado-src` on host)
# primeval
A tool for reconstructing usable RSA keys and cryptographic identities from raw prime factors
