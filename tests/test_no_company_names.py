"""Guard: the artifact stays generic.

This test fails loudly if a denied term appears in any authored text file.
Matching is whole-word: a denied bare word must not trip on benign words that
merely contain it as a substring.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

# SHA-256 digests of lowercase tokens denied from authored text.
_DENIED_DIGESTS = frozenset(
    {
        "0546d8c089e00473d8aa292e4b73607f450b9d0080d77af122b88e200c26a954",
        "30ceaf6d90b3d6edf47d3f675ce1b15aa94b74a7b480c093c34946e77ecee857",
        "33e5d628fc4562d79c6c45dd232ac88262fca67b7d8c9d8bac771ab0b5efe5fa",
        "3a707a22d720cb5ab4143b1f42a7ca05fa38cf38c498cb665c0d43daf8aa95ac",
        "7e5d4325a44714fc86a9b6989e41e966a7297bfe7e913c15fb9ab19588e33d61",
        "b014a0215b719a333d94f3e9f599ff66a75ccfe07964e619adeb221d7ae3b796",
        "c21b962e71f1969d6aea8af9083cc2ec3267ac9c32939d88368ab876f514624d",
        "e1ab66a264e3884b357d951b7aaab396aae5a2fd1e3d87ac695e7dfbbdab1020",
    }
)

_WORD_RE = re.compile(r"[a-z0-9]+")

ROOT = Path(__file__).resolve().parent.parent

# Only scan text we author; skip VCS and tool caches.
SKIP_DIRS = {".git", ".ruff_cache", ".pytest_cache", ".venv", "__pycache__", ".egg-info"}
TEXT_SUFFIXES = {".py", ".md", ".yml", ".yaml", ".toml", ".txt", ".cfg", ".ini", ".json", ".csv", ".sh", ".html"}
EXTENSIONLESS_NAMES = {"LICENSE", "Makefile", "Dockerfile"}


def _iter_text_files():
    for path in ROOT.rglob("*"):
        if any(part in SKIP_DIRS or part.endswith(".egg-info") for part in path.parts):
            continue
        if path.is_file() and (path.suffix in TEXT_SUFFIXES or path.name in EXTENSIONLESS_NAMES):
            yield path


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def test_no_denied_terms_in_repo() -> None:
    offenders: list[str] = []
    for path in _iter_text_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        tokens = set(_WORD_RE.findall(text.lower()))
        hits = sorted(t for t in tokens if _digest(t) in _DENIED_DIGESTS)
        if hits:
            offenders.append(f"{path.relative_to(ROOT)} contains {len(hits)} denied term(s)")
    assert not offenders, "denied terms present: " + "; ".join(offenders)
