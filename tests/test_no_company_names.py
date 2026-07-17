"""Guard: the artifact stays generic. No company/benchmark names anywhere in it.

A specific product or benchmark only ever gets named outside this repo; the
repo itself is deliberately company-agnostic. This test fails loudly if that
ever changes.

Word boundaries matter: the forbidden strings are matched as whole words via
`\\b`, so a benign substring inside another word does not trip the guard. This
file names the forbidden strings, so it excludes only itself from the scan.
"""

from __future__ import annotations

import re
from pathlib import Path

# Whole-word company/benchmark names that must never appear in the repo's files.
FORBIDDEN = ("placetermb", "placetermg")
FORBIDDEN_RE = re.compile(r"\b(" + "|".join(FORBIDDEN) + r")\b", re.IGNORECASE)

ROOT = Path(__file__).resolve().parent.parent

# Only scan text we author; skip VCS and tool caches.
SKIP_DIRS = {".git", ".ruff_cache", ".pytest_cache", ".venv", "__pycache__"}
TEXT_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".toml", ".txt", ".cfg", ".ini", ".json"}


def _iter_text_files():
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in TEXT_SUFFIXES:
            yield path


def test_no_forbidden_company_names_in_repo() -> None:
    # This test file names the forbidden strings; exclude only itself.
    self_path = Path(__file__).resolve()
    offenders: list[str] = []
    for path in _iter_text_files():
        if path.resolve() == self_path:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if FORBIDDEN_RE.search(text):
            hits = sorted({m.group(0).lower() for m in FORBIDDEN_RE.finditer(text)})
            offenders.append(f"{path.relative_to(ROOT)} contains {hits}")
    assert not offenders, "company names leaked into the artifact: " + "; ".join(offenders)


def test_repo_has_fixtures_and_readme() -> None:
    assert (ROOT / "README.md").exists()
    assert len(list((ROOT / "fixtures" / "docs").glob("doc_*.txt"))) == 6
