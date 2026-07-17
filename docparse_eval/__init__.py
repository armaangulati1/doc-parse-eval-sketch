"""A small, self-authored regression eval harness for document-field extraction.

All sample documents are synthetic and invented for this demo. Offline-reproducible.
"""

__all__ = ["extract", "run_eval", "score_field_counts", "aggregate", "prf"]

from .extractor import extract
from .harness import run_eval
from .scoring import aggregate, prf, score_field_counts
