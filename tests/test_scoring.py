from docparse_eval.scoring import aggregate, prf, score_field_counts


def test_prf_perfect():
    assert prf(4, 0, 0) == (1.0, 1.0, 1.0)


def test_prf_empty_field_is_perfect():
    # Nothing in golden and nothing predicted: no way to be wrong.
    assert prf(0, 0, 0) == (1.0, 1.0, 1.0)


def test_prf_over_extraction_drops_precision():
    p, r, f1 = prf(1, 1, 0)
    assert p == 0.5
    assert r == 1.0
    assert 0.66 < f1 < 0.67


def test_prf_missing_drops_recall():
    p, r, f1 = prf(1, 0, 1)
    assert p == 1.0
    assert r == 0.5


def test_over_extraction_on_empty_field_is_a_false_positive():
    golden = [{"notes": None, "line_items": []}]
    pred = [{"notes": "spurious", "line_items": []}]
    counts = score_field_counts(golden, pred)
    assert counts["notes"] == {"tp": 0, "fp": 1, "fn": 0}


def test_line_item_value_mismatch_is_fp_and_fn():
    golden = [{"line_items": [["Revenue", "100"]]}]
    pred = [{"line_items": [["Revenue", "200"]]}]
    counts = score_field_counts(golden, pred)
    assert counts["line_items"] == {"tp": 0, "fp": 1, "fn": 1}


def test_aggregate_perfect_corpus():
    golden = [{
        "company_name": "ACME",
        "period": "Q1 2026",
        "currency": "USD",
        "total_revenue": "100",
        "net_income": "10",
        "notes": None,
        "line_items": [["Revenue", "100"]],
    }]
    per_field, macro = aggregate(score_field_counts(golden, golden))
    assert macro == 1.0
    assert per_field["line_items"]["f1"] == 1.0
