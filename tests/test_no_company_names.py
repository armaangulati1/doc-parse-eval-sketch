"""Guard: this repo is a generic sketch and names no real company or benchmark.

The banned terms are assembled from fragments so the literal strings never
appear in this file (which would otherwise trip the very grep it runs).
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Assembled from fragments on purpose - see the module docstring.
BANNED = [
    "re" + "duc" + "to",
    "rd-" + "table" + "bench",
    "rd" + "table" + "bench",
]

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache"}
TEXT_SUFFIXES = {".py", ".txt", ".json", ".md", ".yml", ".yaml", ".toml", ".cfg"}


def _iter_text_files():
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in TEXT_SUFFIXES:
            yield path


def test_no_banned_terms_anywhere():
    offenders = []
    for path in _iter_text_files():
        content = path.read_text(errors="ignore").lower()
        for term in BANNED:
            if term in content:
                offenders.append((str(path.relative_to(ROOT)), term))
    assert not offenders, f"banned terms found: {offenders}"


def test_repo_has_fixtures_and_readme():
    assert (ROOT / "README.md").exists()
    assert len(list((ROOT / "fixtures" / "docs").glob("doc_*.txt"))) == 6
