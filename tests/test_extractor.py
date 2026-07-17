from pathlib import Path

from docparse_eval.extractor import extract

DOCS = Path(__file__).resolve().parents[1] / "fixtures" / "docs"


def _doc(name):
    return (DOCS / name).read_text()


def test_clean_document_extracts_all_fields():
    result = extract(_doc("doc_01.txt"), mode="baseline")
    assert result["company_name"] == "NORTHWIND MATERIALS INC"
    assert result["period"] == "Q3 2026"
    assert result["currency"] == "USD"
    assert result["total_revenue"] == "1560500"
    assert result["net_income"] == "610300"
    assert result["notes"] == "Figures unaudited."
    assert ["Product Revenue", "1240500"] in result["line_items"]
    assert len(result["line_items"]) == 4


def test_baseline_picks_current_column_on_multi_column_bleed():
    result = extract(_doc("doc_03.txt"), mode="baseline")
    # Current-period (left) values, not the prior-period (right) column.
    assert result["total_revenue"] == "3860000"
    assert result["line_items"] == [
        ["Packaged Goods Revenue", "3120000"],
        ["Fresh Produce Revenue", "740000"],
        ["Cost of Goods Sold", "-1650000"],
    ]


def test_baseline_joins_wrapped_label_row():
    result = extract(_doc("doc_04.txt"), mode="baseline")
    labels = [label for label, _ in result["line_items"]]
    assert "Research and Development Expenses" in labels
    assert "Expenses" not in labels  # no orphan continuation row


def test_baseline_suppresses_empty_placeholder_fields():
    result = extract(_doc("doc_05.txt"), mode="baseline")
    assert result["notes"] is None
    labels = [label for label, _ in result["line_items"]]
    assert "Returns and Allowances" not in labels
    assert len(result["line_items"]) == 3


def test_naive_over_extracts_and_bleeds_columns():
    result = extract(_doc("doc_03.txt"), mode="naive")
    # The naive extractor grabs the prior-period column value.
    assert ["Packaged Goods Revenue", "2890000"] in result["line_items"]


def test_naive_keeps_placeholder_note():
    result = extract(_doc("doc_04.txt"), mode="naive")
    assert result["notes"] == "—"
