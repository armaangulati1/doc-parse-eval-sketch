"""The harness must catch a regression: the naive extractor fails the gate."""

from docparse_eval.cli import main
from docparse_eval.harness import run_eval

GATE = 0.90


def test_baseline_passes_gate():
    assert run_eval(mode="baseline")["macro_f1"] >= GATE


def test_naive_regression_falls_below_gate():
    naive = run_eval(mode="naive")["macro_f1"]
    baseline = run_eval(mode="baseline")["macro_f1"]
    assert naive < GATE, f"naive macro-F1 {naive} should trip the gate"
    assert naive < baseline


def test_naive_degrades_the_planted_edge_case_fields():
    report = run_eval(mode="naive")
    # Multi-column bleed and wrapped-label rows corrupt line items.
    assert report["per_field"]["line_items"]["f1"] < 1.0
    # Over-extraction on empty notes shows up as false positives.
    assert report["per_field"]["notes"]["fp"] > 0


def test_cli_gate_exit_codes():
    assert main(["--extractor", "baseline", "--gate", "0.90"]) == 0
    assert main(["--extractor", "naive", "--gate", "0.90"]) == 1
