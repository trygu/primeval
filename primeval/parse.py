"""Extract modulus and metadata from a public PGP key."""
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path
import sys
import struct
from typing import Optional

import pgpy


DATA_DIR = Path("data")
DEFAULT_METADATA_PATH = DATA_DIR / "metadata.json"


def _extract_pgp_v2(blob: str) -> dict:
    """Manually parse PGP v2/v3 keys that pgpy cannot handle."""
    lines = blob.strip().splitlines()
    b64_lines = []
    in_body = False
    for line in lines:
        if line.startswith("-----BEGIN"):
            in_body = True
            continue
        if line.startswith("-----END"):
            break
        if in_body:
            if not line or line.startswith("="):
                continue
            if ":" in line and not line[0].isspace():
                continue  # armor header
            b64_lines.append(line)

    raw = base64.b64decode("".join(b64_lines))

    n = None
    e = None
    creation = None
    userids = []

    i = 0
    while i < len(raw):
        ctb = raw[i]
        i += 1
        if ctb & 0x80 == 0:
            break
        if ctb & 0x40:  # new format
            tag = ctb & 0x3F
            lb = raw[i]; i += 1
            if lb < 192:
                length = lb
            elif lb < 224:
                length = ((lb - 192) << 8) + raw[i] + 192; i += 1
            else:
                length = struct.unpack(">I", raw[i:i + 4])[0]; i += 4
        else:  # old format
            tag = (ctb & 0x3C) >> 2
            lt = ctb & 0x03
            if lt == 0:
                length = raw[i]; i += 1
            elif lt == 1:
                length = struct.unpack(">H", raw[i:i + 2])[0]; i += 2
            elif lt == 2:
                length = struct.unpack(">I", raw[i:i + 4])[0]; i += 4
            else:
                length = len(raw) - i

        pdata = raw[i:i + length]
        i += length

        if tag == 6 and pdata:  # Public Key
            version = pdata[0]
            if version in (2, 3):
                ts = struct.unpack(">I", pdata[1:5])[0]
                algo = pdata[7]
                creation = str(ts)
                if algo == 1:  # RSA
                    j = 8
                    mpi_bits = struct.unpack(">H", pdata[j:j + 2])[0]; j += 2
                    nb = (mpi_bits + 7) // 8
                    n = int.from_bytes(pdata[j:j + nb], "big"); j += nb
                    mpi_bits_e = struct.unpack(">H", pdata[j:j + 2])[0]; j += 2
                    eb = (mpi_bits_e + 7) // 8
                    e = int.from_bytes(pdata[j:j + eb], "big")
        elif tag == 13:  # User ID
            try:
                userids.append(pdata.decode("utf-8", errors="replace"))
            except Exception:
                pass

    if n is None:
        raise RuntimeError("Could not extract modulus from PGP v2/v3 key")

    return {"n": n, "e": e or 65537, "userids": userids, "created": creation}


def extract(pubpath: Path) -> dict:
    blob = pubpath.read_text()

    # Try pgpy first (handles v4+ keys)
    try:
        key, _ = pgpy.PGPKey.from_blob(blob)
        userids = [str(u) for u in key.userids]
        n = None
        e = None
        creation = None
        try:
            pkt = key._key
            km = getattr(pkt, "keymaterial", pkt)
            n = int(getattr(km, "n"))
            e = int(getattr(km, "e"))
            creation = str(key.created)
        except Exception:
            pass
        if n is not None:
            return {"n": n, "e": e or 65537, "userids": userids, "created": creation}
    except Exception:
        pass

    # Fallback: manual parser for PGP v2/v3
    return _extract_pgp_v2(blob)


def write_metadata(metadata: dict, output: Path = DEFAULT_METADATA_PATH) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metadata))
    return output


def build_parser(prog: str = "primeval parse") -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Extract RSA modulus metadata from an ASCII-armored OpenPGP public key.",
    )
    parser.add_argument("public_key", metavar="KEY", type=Path)
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_METADATA_PATH,
        help=f"metadata output path (default: {DEFAULT_METADATA_PATH})",
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

    pub = args.public_key
    if not pub.exists():
        print("Public key not found:", pub, file=sys.stderr)
        return 3

    try:
        md = extract(pub)
    except Exception as exc:
        print("Failed to extract:", exc, file=sys.stderr)
        return 4

    output = write_metadata(md, args.output)
    print("Wrote", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
