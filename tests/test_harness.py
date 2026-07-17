from docparse_eval.harness import load_fixtures, run_eval


def test_fixtures_load():
    fixtures = load_fixtures()
    assert len(fixtures) == 6
    for _doc_id, text, golden in fixtures:
        assert text.strip()
        assert "line_items" in golden


def test_baseline_matches_golden_exactly():
    report = run_eval(mode="baseline")
    assert report["n_docs"] == 6
    assert report["macro_f1"] == 1.0
    for field, metrics in report["per_field"].items():
        assert metrics["f1"] == 1.0, field
        assert metrics["fp"] == 0, field
        assert metrics["fn"] == 0, field
