"""Per-field precision / recall / F1 scoring against a golden set.

Every extracted field value is treated as set membership so that:

* a correct value is a true positive,
* a value present in the prediction but not the golden set (a wrong value or a
  spurious value on an empty field) is a false positive (over-extraction),
* a value present in the golden set but missing from the prediction is a false
  negative.

Macro-F1 is the unweighted mean of per-field F1 across all fields.
"""

SCALAR_FIELDS = (
    "company_name",
    "period",
    "currency",
    "total_revenue",
    "net_income",
    "notes",
)
ALL_FIELDS = SCALAR_FIELDS + ("line_items",)


def _scalar_sets(field, golden_value, pred_value):
    golden = {(field, golden_value)} if golden_value is not None else set()
    pred = {(field, pred_value)} if pred_value is not None else set()
    return golden, pred


def _item_set(items):
    return {(str(label).lower().strip(), str(amount)) for label, amount in (items or [])}


def score_field_counts(golden_docs, pred_docs):
    """Aggregate TP/FP/FN per field across a corpus."""
    counts = {field: {"tp": 0, "fp": 0, "fn": 0} for field in ALL_FIELDS}
    for golden, pred in zip(golden_docs, pred_docs):
        for field in SCALAR_FIELDS:
            gset, pset = _scalar_sets(field, golden.get(field), pred.get(field))
            counts[field]["tp"] += len(gset & pset)
            counts[field]["fp"] += len(pset - gset)
            counts[field]["fn"] += len(gset - pset)
        gset = _item_set(golden.get("line_items"))
        pset = _item_set(pred.get("line_items"))
        counts["line_items"]["tp"] += len(gset & pset)
        counts["line_items"]["fp"] += len(pset - gset)
        counts["line_items"]["fn"] += len(gset - pset)
    return counts


def prf(tp, fp, fn):
    """Precision, recall, F1. A field with nothing to predict scores 1.0."""
    if tp + fp + fn == 0:
        return 1.0, 1.0, 1.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def aggregate(counts):
    """Return (per_field metrics dict, macro_f1)."""
    per_field = {}
    f1_scores = []
    for field, count in counts.items():
        precision, recall, f1 = prf(count["tp"], count["fp"], count["fn"])
        per_field[field] = {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            **count,
        }
        f1_scores.append(f1)
    macro_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0.0
    return per_field, macro_f1
