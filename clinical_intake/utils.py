"""Shared utility functions for data normalization.

These functions normalize raw LLM output at the pipeline level so CSVs
always contain clean, consistent values. The dashboard may apply thin
display-oriented wrappers (e.g., swapping empty strings for em-dashes).

Exports:
    normalize_sex: Normalize sex string to "M" or "F".
    normalize_age: Extract the numeric portion from an age string.
"""

import re
from typing import Any


def normalize_sex(value: Any) -> str:
    """Normalize sex to M or F.

    Handles ``Male``, ``Female``, ``male``, ``female``, ``M``, ``F``
    and any case variation. Returns empty string for unrecognized values.

    Args:
        value: The raw sex value from the LLM output.

    Returns:
        ``"M"``, ``"F"``, or ``""``.
    """
    v = str(value).strip().lower() if value else ""
    if v in ("m", "male"):
        return "M"
    if v in ("f", "female"):
        return "F"
    return value or ""


def normalize_age(value: Any) -> str:
    """Extract just the number from an age string.

    Handles formats like ``"45-year-old"``, ``"30 yo male"``, ``"80"``,
    ``None``, and redacted markers (``___``, ``[Redacted]``, etc.).

    Args:
        value: The raw age value from the LLM output.

    Returns:
        The numeric age as a string (e.g. ``"45"``), or ``""`` if no
        recognizable age is found.
    """
    v = str(value).strip() if value else ""
    if not v or v.lower() in ("___", "[redacted]", "nan", "none", "n/a", "-", "unk"):
        return ""
    m = re.search(r"\b(\d{1,3})\b", v)
    return m.group(1) if m else ""
