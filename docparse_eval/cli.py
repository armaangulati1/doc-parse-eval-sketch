"""Command-line entry point and CI gate.

    python -m docparse_eval.cli --extractor baseline --gate 0.90

Exits non-zero when macro-F1 falls below the gate, so CI fails on a regression.
"""

import argparse
import sys

from .harness import run_eval


def _print_report(report):
    print(f"extractor: {report['mode']}   documents: {report['n_docs']}")
    print(f"{'field':<22}{'precision':>11}{'recall':>9}{'f1':>9}"
          f"{'tp':>5}{'fp':>5}{'fn':>5}")
    for field, metrics in report["per_field"].items():
        print(
            f"{field:<22}{metrics['precision']:>11.3f}{metrics['recall']:>9.3f}"
            f"{metrics['f1']:>9.3f}{metrics['tp']:>5}{metrics['fp']:>5}{metrics['fn']:>5}"
        )
    print(f"{'macro-F1':<22}{report['macro_f1']:>29.4f}")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Document-extraction regression eval.")
    parser.add_argument(
        "--extractor", default="baseline", choices=["baseline", "naive"]
    )
    parser.add_argument("--gate", type=float, default=0.90)
    parser.add_argument("--fixtures", default=None)
    args = parser.parse_args(argv)

    report = run_eval(mode=args.extractor, fixtures_dir=args.fixtures)
    _print_report(report)

    if report["macro_f1"] < args.gate:
        print(f"\nGATE FAILED: macro-F1 {report['macro_f1']:.4f} < {args.gate}")
        return 1
    print(f"\nGATE PASSED: macro-F1 {report['macro_f1']:.4f} >= {args.gate}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
