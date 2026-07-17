"""Load fixtures, run an extractor over them, and score against the golden set."""

import json
from pathlib import Path

from .extractor import extract
from .scoring import aggregate, score_field_counts

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def load_fixtures(fixtures_dir=None):
    """Return a list of (doc_id, raw_text, golden_dict)."""
    base = Path(fixtures_dir) if fixtures_dir else FIXTURES
    out = []
    for doc_path in sorted((base / "docs").glob("doc_*.txt")):
        doc_id = doc_path.stem
        golden = json.loads((base / "golden" / f"{doc_id}.json").read_text())
        out.append((doc_id, doc_path.read_text(), golden))
    return out


def run_eval(mode="baseline", fixtures_dir=None):
    """Run an extractor over every fixture and return a report dict."""
    fixtures = load_fixtures(fixtures_dir)
    golden_docs, pred_docs, ids = [], [], []
    for doc_id, text, golden in fixtures:
        golden_docs.append(golden)
        pred_docs.append(extract(text, mode=mode))
        ids.append(doc_id)
    counts = score_field_counts(golden_docs, pred_docs)
    per_field, macro_f1 = aggregate(counts)
    return {
        "mode": mode,
        "n_docs": len(ids),
        "ids": ids,
        "per_field": per_field,
        "macro_f1": macro_f1,
    }
