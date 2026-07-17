# doc-parse-eval-sketch

A small, self-authored demonstration of a regression eval harness for
document-field extraction. All sample documents are synthetic and invented for
this demo. Not affiliated with any company; not built on any company's data or
benchmark. Demo scope, self-authored synthetic data, offline-reproducible.

## What it does

It scores a document-extraction workflow against a hand-authored golden set,
field by field, and gates continuous integration on the result. If a change
makes extraction worse, the macro-F1 gate drops below its threshold and CI
fails. That is the whole point: a parsing pipeline can regress silently, and a
regression eval turns "it looks fine" into a number that either holds or does
not.

The task is a table-heavy quarterly financial statement. Each fixture is the
raw text a parser would emit; the harness extracts structured fields
(`company_name`, `period`, `currency`, `total_revenue`, `net_income`, `notes`,
and a `line_items` table) and compares them to the golden set.

## The edge cases it targets

Most extraction demos only measure the easy path. This harness plants the
ambiguous cases that quietly break real document parsing, one per fixture, and
proves the harness catches them:

- **Multi-column bleed** (`doc_03`, `doc_06`): a prior-period column sits beside
  the current one, so a naive linear read grabs the wrong number.
- **Table-structure ambiguity** (`doc_04`): a line-item label wraps onto a
  second, indented row, so a naive row parser splits one item into two.
- **Over-extraction on sparse / empty fields** (`doc_04`, `doc_05`): an empty
  note and a dash-placeholder line item invite a parser to invent a value.

`doc_01` and `doc_02` are clean controls.

## Scoring

Each field value is treated as set membership against the golden set:

- correct value -> true positive,
- value predicted but wrong, or invented on an empty field -> false positive
  (this is how over-extraction is penalized),
- value in the golden set but missing -> false negative.

Per-field precision / recall / F1 are aggregated across the corpus, and
**macro-F1** is the unweighted mean of per-field F1. The CI gate fails below a
configurable threshold (default `0.90`).

## Two extractors (how the regression is demonstrated)

- `baseline` is a rule-based extractor written to handle the three edge cases.
  On the six self-authored fixtures it scores **1.000** precision / recall / F1
  per field (macro-F1 `1.0000`).
- `naive` is a deliberately simpler extractor with three known bugs
  (last-number-on-line, no wrapped-label joining, no empty-field suppression).
  It scores below the gate, which is exactly the regression the harness is meant
  to catch. `tests/test_regression_gate.py` asserts the gate would fail.

The `1.000` figure is precision / recall / F1 of the baseline on its own
six-fixture self-authored set. It reflects agreement between the extractor and
the golden labels on this small invented corpus, not a general accuracy claim.

## Run it

```bash
pip install -r requirements.txt

# Run the eval + CI gate on the working extractor (exit 0):
python -m docparse_eval.cli --extractor baseline --gate 0.90

# Show the gate catching a regression (exit 1):
python -m docparse_eval.cli --extractor naive --gate 0.90

# Tests + lint:
pytest -q
ruff check .
```

Everything above runs offline with no API key.

## Optional live extractor

`docparse_eval/extractor.py` includes an optional `llm_extract` path that calls
a model when `ANTHROPIC_API_KEY` is set. It is a sketch of how a live model
would slot into the same schema and gate. It is intentionally excluded from the
tests and the CI gate, and it has not been run against a live model in this
demo.

## Layout

```
docparse_eval/
  extractor.py   baseline + naive (buggy) + optional llm extractors
  scoring.py     per-field precision / recall / F1, macro-F1
  harness.py     load fixtures, run an extractor, score
  cli.py         eval report + CI gate (exit code)
fixtures/
  docs/          six synthetic financial-statement documents
  golden/        hand-authored expected fields per document
tests/           deterministic offline tests + a banned-terms guard
```

## Scope and honesty

This is a demo scaffold, not a deployed system. The documents are invented,
the golden set is self-authored, and the metrics describe this small synthetic
corpus only. It demonstrates the shape of a regression eval harness: fixtures
with planted edge cases, per-field metrics, and a CI gate that fails on
regression.
