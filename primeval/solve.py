"""solve.py - parse factorization output and write p.txt/q.txt

Usage: uv run solve.py data/factorization.log
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

DATA_DIR = Path("data")


P_RE = re.compile(r"\bp\s*[=:]\s*([0-9]{3,})\b", re.IGNORECASE)
Q_RE = re.compile(r"\bq\s*[=:]\s*([0-9]{3,})\b", re.IGNORECASE)
INT_RE = re.compile(r"\b([0-9]{10,})\b")


def parse_log(path: Path) -> tuple[int, int]:
    text = path.read_text(errors="ignore")
    p = None
    q = None

    m = P_RE.search(text)
    if m:
        p = int(m.group(1))
    m = Q_RE.search(text)
    if m:
        q = int(m.group(1))

    # fallback: find large ints; handle CADO output "N p q" (N = p*q on same line)
    if not p or not q:
        ints = [int(x) for x in INT_RE.findall(text)]
        unique = list(dict.fromkeys(ints))  # deduplicate, preserve order
        if len(unique) >= 3 and unique[0] == unique[1] * unique[2]:
            # First number is N, next two are factors
            p, q = unique[1], unique[2]
        elif len(unique) >= 2:
            p, q = unique[0], unique[1]

    if not p or not q:
        raise RuntimeError("Could not find p and q in log")

    return p, q


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if len(argv) < 1:
        print("Usage: solve.py path/to/factorization.log")
        return 2

    path = Path(argv[0])
    if not path.exists():
        print("Log file not found:", path)
        return 3

    try:
        p, q = parse_log(path)
    except Exception as exc:
        print("Failed to parse factors:", exc)
        return 4

    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "p.txt").write_text(str(p))
    (DATA_DIR / "q.txt").write_text(str(q))
    print("Wrote data/p.txt and data/q.txt")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
