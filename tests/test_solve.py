"""Tests for solve.py - CADO-NFS log parsing."""
from pathlib import Path
import pytest
from primeval.solve import parse_log


# Small primes for label-based parsing tests (P_RE/Q_RE)
P_SMALL = 961748941
Q_SMALL = 982451653

# Large primes (~20 digits) for fallback/INT_RE tests — realistic CADO output size
P_LARGE = 94418953280491177
Q_LARGE = 98750105931942169
N_LARGE = P_LARGE * Q_LARGE


def write_log(tmp_path: Path, content: str) -> Path:
    log = tmp_path / "factorization.log"
    log.write_text(content)
    return log


def test_parse_explicit_p_q(tmp_path):
    """p = X / q = Y format (simple/simulated output)."""
    log = write_log(tmp_path, f"p = {P_SMALL}\nq = {Q_SMALL}\n")
    p, q = parse_log(log)
    assert p == P_SMALL
    assert q == Q_SMALL


def test_parse_cado_final_line(tmp_path):
    """CADO-NFS real output: stdout is 'p q' space-separated, N appears earlier in log."""
    log = write_log(tmp_path, (
        f"Info:root: Command line parameters: cado-nfs.py {N_LARGE} --workdir /work\n"
        "Info:Complete Factorization: Total cpu/elapsed time for entire factorization: 123.4\n"
        f"{P_LARGE} {Q_LARGE}\n"
    ))
    p, q = parse_log(log)
    assert {p, q} == {P_LARGE, Q_LARGE}


def test_parse_cado_with_prp_labels(tmp_path):
    """CADO-NFS sometimes labels factors as prp<digits>."""
    log = write_log(tmp_path, (
        f"Info:root: {N_LARGE} = prp17 * prp17\n"
        f"{P_LARGE}\n"
        f"{Q_LARGE}\n"
    ))
    p, q = parse_log(log)
    assert {p, q} == {P_LARGE, Q_LARGE}


def test_parse_large_integers_fallback(tmp_path):
    """Fallback: picks first two large integers when labels absent."""
    log = write_log(tmp_path, f"Result: {P_LARGE} {Q_LARGE}\n")
    p, q = parse_log(log)
    assert {p, q} == {P_LARGE, Q_LARGE}


def test_parse_factors_txt(tmp_path):
    """factors.txt format: stdout-only capture, just 'p q' on one line, no N."""
    log = write_log(tmp_path, f"{P_LARGE} {Q_LARGE}\n")
    p, q = parse_log(log)
    assert {p, q} == {P_LARGE, Q_LARGE}


def test_parse_missing_factors_raises(tmp_path):
    log = write_log(tmp_path, "No factors here.\n")
    with pytest.raises(RuntimeError):
        parse_log(log)
