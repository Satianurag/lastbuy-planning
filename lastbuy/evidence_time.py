"""Conservative currentness checks for numeric evidence with explicit time labels.

This does not infer an authoritative balance from prose. It refuses to use a
number explicitly labeled opening/historical/superseded as the current fact.
The surrounding source sentence is checked even when the quotation omits labels.
"""

import re
from decimal import Decimal, InvalidOperation

NUMBER = re.compile(r"(?<![\w.-])\d[\d,]*(?:\.\d+)?(?![\w-]|\.\d)")
HISTORICAL = re.compile(
    r"\b(opening|historical|previous|prior|earlier|superseded|obsolete|original)\b",
    re.I,
)
CURRENT = re.compile(r"\b(current|currently|closing|remaining|revised|now)\b", re.I)
BOUNDARY = re.compile(r"[.!?;](?=\s|$)|\n")


def historical_numeric_support(check, sources):
    """True only if every quoted occurrence of the selected number is historical."""
    observed = check.get("observed_value")
    if observed is None:
        return False
    try:
        value = Decimal(observed.replace(",", ""))
    except (InvalidOperation, AttributeError):
        return False
    occurrences = []
    for quote in check.get("supporting_quotes", []):
        full = sources.get(quote["source_id"], "")
        selected = quote["quote"]
        if not selected:
            continue
        offset = full.find(selected)
        while offset >= 0:
            for match in NUMBER.finditer(selected):
                if Decimal(match.group().replace(",", "")) != value:
                    continue
                position = offset + match.start()
                boundaries = list(BOUNDARY.finditer(full[:position]))
                start = boundaries[-1].end() if boundaries else 0
                prefix = full[start:position]
                history = list(HISTORICAL.finditer(prefix))
                current = list(CURRENT.finditer(prefix))
                occurrences.append(
                    bool(history)
                    and (not current or history[-1].start() > current[-1].start())
                )
            offset = full.find(selected, offset + 1)
    return bool(occurrences) and all(occurrences)


def historical_plan_checks(plan, snapshot):
    sources = {s.id: s.text for s in snapshot.sources}
    return [
        check["key"]
        for result in plan.get("assessments", [])
        for check in result.get("assessment", {}).get("checks", [])
        if historical_numeric_support(check, sources)
    ]
