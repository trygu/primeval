# Primeval

[![CI](https://github.com/trygu/primeval/actions/workflows/ci.yml/badge.svg)](https://github.com/trygu/primeval/actions/workflows/ci.yml)

A tool for reconstructing RSA/OpenPGP private keys from raw prime factors.
Given a PGP public key whose RSA modulus can be factored, Primeval extracts
the modulus, runs CADO-NFS to find p and q, and assembles a valid RSA private
key (PEM format).

> **WARNING:** Reconstructed private keys are highly sensitive. Treat all
> output files with extreme care — restrict file permissions, use encrypted
> storage, and securely delete when no longer needed.

---

## Requirements

- Python 3.10–3.12 (pgpy is not yet compatible with 3.13+)
- [uv](https://docs.astral.sh/uv/) — install with `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Docker + Docker Compose (for CADO-NFS)
- **Linux x86_64 host** for the factorization step — the official CADO-NFS
  image uses AVX2/AVX-512 instructions and will crash with "Illegal
  instruction" under Rosetta 2 on Apple Silicon

---

## Full walkthrough

### 1. Set up Python environment

```bash
uv sync --extra dev
```

uv creates `.venv` automatically and installs all dependencies from `uv.lock`.

### 2. Extract modulus from the public key

```bash
python -m primeval.parse primeval/publickey.asc
```

Writes:

- `data/modulus.txt` — the RSA modulus N as a decimal integer
- `data/metadata.json` — key metadata (creation date, exponent e, etc.)

### 3. Start the CADO-NFS container

```bash
docker compose up --build -d
```

The container mounts `./data` as `/work` inside the container and idles until
you run a command in it. Build only happens on first run.

### 4. Run factorization

```bash
N=$(cat data/modulus.txt)
docker compose exec cado-engine bash -c \
  "cado-nfs.py $N --workdir /work/work \
   2> >(tee /work/factorization.log >&2) \
   | tee /work/factors.txt"
```

- `data/factors.txt` — stdout from CADO-NFS, contains just `p q` on the last line
- `data/factorization.log` — full stderr progress log (sieve, linear algebra, etc.)
- `data/work/` — CADO-NFS intermediate files (can be resumed if interrupted)

Factoring a 155-digit number typically takes several hours on a modern server.
You can interrupt and resume: CADO-NFS saves state in `data/work/`.

### 5. Extract p and q

```bash
python -m primeval.solve data/factors.txt
```

Falls back to parsing the full log if needed:

```bash
python -m primeval.solve data/factorization.log
```

Writes:

- `data/p.txt`
- `data/q.txt`

### 6. Reconstruct the private key

```bash
python -m primeval.reconstruct
```

Validates that `p * q == N`, then writes `private_key.asc` as a PEM-encoded
RSA private key. Despite the `.asc` name, this is not OpenPGP ASCII armor; it
is a plain text PEM file containing ASCII lines such as
`-----BEGIN RSA PRIVATE KEY-----`. The file is created in the current working
directory.

---

## Project structure

```
primeval/
  parse.py        — extracts modulus + metadata from PGP public key
  solve.py        — parses CADO-NFS output to find p and q
  reconstruct.py  — assembles RSA private key from p, q, e
  publickey.asc   — the target PGP public key
data/
  modulus.txt     — N (written by parse.py)
  metadata.json   — key metadata (written by parse.py)
  factors.txt     — CADO-NFS stdout: "p q" (written during factorization)
  factorization.log — full CADO-NFS progress log
  work/           — CADO-NFS intermediate state (resumable)
cado-src/
  Dockerfile      — wraps registry.gitlab.inria.fr/cado-nfs/cado-nfs/factoring-full:latest
  entrypoint.sh   — minimal entrypoint (mkdir /work; exec "$@")
tests/            — pytest suite (14 tests)
```

---

## Development

Run tests:

```bash
uv run pytest
```

Key test files:

- `tests/test_solve.py` — unit tests for log parsing logic
- `tests/test_parse.py` — unit tests for PGP key parsing
- `tests/test_reconstruct.py` — unit tests for RSA key assembly
- `tests/test_reconstruction.py` — integration test with a generated 1024-bit key
