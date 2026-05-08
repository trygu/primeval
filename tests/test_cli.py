import json
from pathlib import Path

from cryptography.hazmat.primitives.serialization import load_pem_private_key

from primeval.cli import main as cli_main


P = 961748941
Q = 982451653
E = 65537
N = P * Q
PUBKEY_ASC = Path(__file__).parent.parent / "primeval" / "publickey.asc"


def test_cli_parse_writes_custom_metadata(tmp_path):
    out = tmp_path / "metadata.json"

    rv = cli_main(["parse", str(PUBKEY_ASC), "-o", str(out)])

    assert rv == 0
    md = json.loads(out.read_text())
    assert int(md["n"]) > 0
    assert int(md["e"]) > 0


def test_cli_modulus_prints_n(tmp_path, capsys):
    metadata = tmp_path / "metadata.json"
    metadata.write_text(json.dumps({"n": N, "e": E}))

    rv = cli_main(["modulus", "-m", str(metadata)])

    assert rv == 0
    assert capsys.readouterr().out.strip() == str(N)


def test_cli_factors_extracts_and_validates_pair(tmp_path):
    metadata = tmp_path / "metadata.json"
    source = tmp_path / "factorization.log"
    p_path = tmp_path / "p.txt"
    q_path = tmp_path / "q.txt"
    metadata.write_text(json.dumps({"n": N, "e": E}))
    source.write_text(f"noise 2026 17\nfactor: {P}\nfactor: {Q}\n")

    rv = cli_main(
        [
            "import-factors",
            str(source),
            "-m",
            str(metadata),
            "-p",
            str(p_path),
            "-q",
            str(q_path),
        ]
    )

    assert rv == 0
    assert int(p_path.read_text()) == P
    assert int(q_path.read_text()) == Q


def test_cli_reconstruct_accepts_custom_paths(tmp_path):
    metadata = tmp_path / "metadata.json"
    p_path = tmp_path / "p.txt"
    q_path = tmp_path / "q.txt"
    out = tmp_path / "private_key.pem"
    metadata.write_text(json.dumps({"n": N, "e": E}))
    p_path.write_text(str(P))
    q_path.write_text(str(Q))

    rv = cli_main(
        [
            "reconstruct",
            "-m",
            str(metadata),
            "-p",
            str(p_path),
            "-q",
            str(q_path),
            "-o",
            str(out),
        ]
    )

    assert rv == 0
    key = load_pem_private_key(out.read_bytes(), password=None)
    assert key.public_key().public_numbers().n == N
