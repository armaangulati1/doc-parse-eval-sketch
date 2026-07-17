"""Field extractors for the synthetic financial-statement documents.

Two offline extractors are provided:

* ``baseline`` - a rule-based extractor written to handle the edge cases the
  fixtures plant (multi-column bleed, wrapped-label table rows, and empty /
  placeholder fields).
* ``naive`` - a deliberately simpler extractor whose known bugs fail exactly
  those edge cases. It exists so the harness can demonstrate that the CI gate
  catches a regression.

An optional ``llm`` extractor is included but is never exercised by the offline
tests or the CI gate; it only runs when ``ANTHROPIC_API_KEY`` is set.
"""

import re

# A line item with a real amount:  "<label>  <amount>" (2+ spaces, then digits).
AMOUNT_RE = re.compile(r"^\s*(.+?)\s{2,}(-?[\d,]+)(?:\s|$)")
# A field with an empty / placeholder value: "<label>  —" (or -, N/A, TBD ...).
PLACEHOLDER_RE = re.compile(r"^\s*(.+?)\s{2,}(—|–|-|N/A|n/a|TBD)\s*$")
NUMBER_RE = re.compile(r"-?[\d,]+")
PLACEHOLDERS = {"", "—", "–", "-", "N/A", "n/a", "TBD"}


def _norm_amount(raw):
    return raw.replace(",", "").strip()


def _clean(text):
    return re.sub(r"\s+", " ", text).strip()


def _first_nonempty(lines):
    for line in lines:
        if line.strip():
            return line.strip()
    return None


def _period(text):
    match = re.search(r"Period:\s*(Q\d\s+\d{4})", text)
    return match.group(1) if match else None


def _currency(text):
    match = re.search(r"Currency:\s*([A-Z]{3})", text)
    return match.group(1) if match else None


def _scalar_amount(text, label, pick_last=False):
    for line in text.splitlines():
        match = re.match(rf"^\s*{re.escape(label)}\s+(-?[\d,]+)", line)
        if match:
            if pick_last:
                # BUG (naive): grabs the right-most number, i.e. a prior-period
                # column, when a statement bleeds two columns onto one line.
                return _norm_amount(NUMBER_RE.findall(line)[-1])
            return _norm_amount(match.group(1))
    return None


def _notes(text, suppress=True):
    match = re.search(r"^\s*Notes:\s*(.*)$", text, re.MULTILINE)
    if not match:
        return None
    value = match.group(1).strip()
    if suppress and value in PLACEHOLDERS:
        return None
    return value or None


def _section_lines(text):
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.lstrip().startswith("LINE ITEMS"):
            start = i + 1
            break
    if start is None:
        return []
    out = []
    for line in lines[start:]:
        if not line.strip():
            break
        out.append(line)
    return out


def _baseline_items(section):
    """Handles wrapped-label rows, empty placeholders, and column bleed."""
    items = []
    i = 0
    while i < len(section):
        line = section[i]
        if not line.strip():
            i += 1
            continue
        amount = AMOUNT_RE.match(line)
        if amount:
            items.append([_clean(amount.group(1)), _norm_amount(amount.group(2))])
            i += 1
            continue
        if PLACEHOLDER_RE.match(line):
            # Empty / placeholder value: suppress it (do not over-extract).
            i += 1
            continue
        # A bare label with no amount: join it with the next indented row.
        if i + 1 < len(section) and section[i + 1].startswith(("  ", "\t")):
            nxt = AMOUNT_RE.match(section[i + 1])
            if nxt:
                label = _clean(line) + " " + _clean(nxt.group(1))
                items.append([label, _norm_amount(nxt.group(2))])
                i += 2
                continue
        i += 1
    return items


def _naive_items(section):
    """Deliberately buggy: last-number, no continuation, no suppression."""
    items = []
    for line in section:
        if not line.strip():
            continue
        numbers = NUMBER_RE.findall(line)
        if numbers:
            first = NUMBER_RE.search(line)
            label = _clean(line[: first.start()])
            # BUG: picks the last number on the line (prior-period column).
            items.append([label, _norm_amount(numbers[-1])])
        else:
            parts = re.split(r"\s{2,}", line.strip(), maxsplit=1)
            if len(parts) == 2:
                # BUG: emits a value for an empty / placeholder field.
                items.append([_clean(parts[0]), parts[1].strip()])
            # A bare wrapped label with no amount is silently dropped (BUG).
    return items


def extract(text, mode="baseline"):
    """Return a field dict for a document. ``mode`` is 'baseline' or 'naive'."""
    if mode not in ("baseline", "naive"):
        raise ValueError(f"unknown extractor mode: {mode!r}")
    section = _section_lines(text)
    if mode == "baseline":
        items = _baseline_items(section)
        notes = _notes(text, suppress=True)
        pick_last = False
    else:
        items = _naive_items(section)
        notes = _notes(text, suppress=False)
        pick_last = True
    return {
        "company_name": _first_nonempty(text.splitlines()),
        "period": _period(text),
        "currency": _currency(text),
        "total_revenue": _scalar_amount(text, "Total Revenue", pick_last),
        "net_income": _scalar_amount(text, "Net Income", pick_last),
        "notes": notes,
        "line_items": items,
    }


def llm_extract(text):  # pragma: no cover - optional, never run offline
    """Optional thin LLM extractor. Requires ANTHROPIC_API_KEY; not used by CI.

    This path is intentionally excluded from the offline tests and the CI gate.
    It is a sketch of how a live model call would slot into the same schema.
    """
    import json
    import os

    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set; the offline demo uses --extractor baseline/naive"
        )
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("the optional 'anthropic' package is not installed") from exc

    client = anthropic.Anthropic(api_key=key)
    schema = (
        "Return ONLY JSON with keys: company_name, period, currency, "
        "total_revenue, net_income, notes, line_items (list of [label, amount]). "
        "Amounts are digit strings with no commas; notes is null when blank.\n\n"
    )
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": schema + text}],
    )
    return json.loads(message.content[0].text)
