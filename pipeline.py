"""
Batch CSV processor — runs the extraction pipeline over every row in a CSV.

Reads a CSV with 'text' and 'summary' columns. The **summary** column
is passed to the LLM for extraction (faster, smaller). Both the original
'text' and 'summary' are preserved in the output CSV for reference.

Usage:
    python -m pipeline data/sample.csv data/output_sample.csv
"""

import csv
import os
import random
import re
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Optional

from langchain_openai import ChatOpenAI
from langchain_core.runnables import Runnable

from clinical_intake.chain import build_chain
from pydantic import BaseModel

from clinical_intake.schemas import ClinicalIntake


def _serialize(val: Any) -> str:
    """Convert a single value to a string safe for CSV output.

    Handles None, enums, and everything else uniformly.
    """
    if val is None:
        return ""
    if isinstance(val, Enum):
        return val.value
    return str(val)


_FLAT_COLUMNS_CACHE: list[str] | None = None


def _get_flat_columns() -> list[str]:
    """Derive flattened column names from the ClinicalIntake schema.

    Results are cached after first call since the schema is static.
    """
    global _FLAT_COLUMNS_CACHE
    if _FLAT_COLUMNS_CACHE is not None:
        return _FLAT_COLUMNS_CACHE

    columns = []
    for field_name, field_info in ClinicalIntake.model_fields.items():
        # Check if the field's annotation is a nested BaseModel
        origin = field_info.annotation
        # Unwrap Optional[T] to get T
        args = getattr(origin, "__args__", None)
        if args:
            # Optional[X] → use X
            inner = next((a for a in args if a is not type(None)), origin)
        else:
            inner = origin

        # Check if inner is a BaseModel subclass
        if isinstance(inner, type) and issubclass(inner, BaseModel):
            for sub_name in inner.model_fields:
                columns.append(f"{field_name}_{sub_name}")
        else:
            columns.append(field_name)
    _FLAT_COLUMNS_CACHE = columns
    return columns


def _flatten_intake(result: ClinicalIntake) -> dict[str, str]:
    """Flatten a nested ClinicalIntake object into flat column→value pairs.

    Nested models become ``parent_child`` column names, lists become
    semicolon-separated strings, and None/empty becomes an empty string.
    """
    flat = {}
    # mode="json" ensures enums serialize as their string values
    data = result.model_dump(mode="json")
    for key, value in data.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                col = f"{key}_{sub_key}"
                if isinstance(sub_value, list):
                    flat[col] = "; ".join(str(v) for v in sub_value) if sub_value else ""
                else:
                    val = _normalize_sex(sub_value) if sub_key == "sex" else _normalize_age(sub_value) if sub_key == "age" else _serialize(sub_value)
                    flat[col] = val
        elif isinstance(value, list):
            flat[key] = "; ".join(str(v) for v in value) if value else ""
        elif value is None:
            # Nested model was None — fill all its sub-fields as empty
            for col in _get_flat_columns():
                if col.startswith(f"{key}_"):
                    flat[col] = ""
        else:
            flat[key] = _serialize(value)
    return flat


def _normalize_sex(value: Any) -> str:
    """Normalize sex to M or F. Handles Male/Female/male/female/M/F."""
    v = str(value).strip().lower() if value else ""
    if v in ("m", "male"):
        return "M"
    if v in ("f", "female"):
        return "F"
    return value or ""


def _normalize_age(value: Any) -> str:
    """Extract just the number from an age string.

    Handles formats like '45-year-old', '30 yo male', '80', None, etc.
    """
    v = str(value).strip() if value else ""
    if not v or v.lower() in ("___", "[redacted]", "nan", "none", "n/a", "-", "unk"):
        return ""
    m = re.search(r"\b(\d{1,3})\b", v)
    return m.group(1) if m else ""


def _process_one_row(chain: Runnable, row: dict[str, Any]) -> tuple[dict[str, str], str]:
    """Run extraction on a single row. Returns (extracted_dict, error_message)."""
    try:
        result = chain.invoke({"note_text": row["summary"]})
        return _flatten_intake(result), ""
    except Exception as exc:
        return {}, f"{type(exc).__name__}: {exc}"


def process_csv(
    src: str | Path,
    dst: str | Path,
    *,
    limit: Optional[int] = None,
    concurrent: int = 1,
    model: str = "deepseek-v4-flash",
    base_url: str = "https://api.deepseek.com",
    api_key: Optional[str] = None,
) -> None:
    """Read a CSV of notes, extract intake data, write annotated CSV.

    Builds the extraction chain once (not once per row), processes each
    note in parallel if ``concurrent > 1``, flattens the structured output into new columns, and captures
    per-row errors in an ``error`` column.

    Args:
        src: Path to input CSV (must have 'text' and 'summary' columns).
        dst: Path to output CSV (original columns + extracted fields).
        limit: Optional max rows to process (for testing).
        concurrent: Number of parallel extraction workers (default 1 = sequential).
        model: LLM model name.
        base_url: API base URL.
        api_key: DeepSeek API key (falls back to DEEPSEEK_API_KEY env var).
    """
    resolved_key = api_key or os.getenv("DEEPSEEK_API_KEY")
    if not resolved_key:
        raise ValueError(
            "DEEPSEEK_API_KEY not set. Provide api_key or set the DEEPSEEK_API_KEY "
            "environment variable."
        )

    llm = ChatOpenAI(
        model=model,
        base_url=base_url,
        api_key=resolved_key,
        temperature=0.0,
    )
    chain = build_chain(llm)

    src_path = Path(src)
    dst_path = Path(dst)
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    with src_path.open("r", newline="", encoding="utf-8") as fin:
        reader = csv.DictReader(fin)
        all_rows = list(reader)

    rows_to_process = all_rows[:limit] if limit else all_rows

    # Derive flattened column names from the schema (no API call needed)
    extracted_columns = _get_flat_columns()

    fieldnames = ["patient_id", "text", "summary", *extracted_columns, "error"]

    results = [{} for _ in rows_to_process]

    if concurrent > 1:
        with ThreadPoolExecutor(max_workers=concurrent) as pool:
            futures = {
                pool.submit(_process_one_row, chain, row): i
                for i, row in enumerate(rows_to_process)
            }
            for future in as_completed(futures):
                i = futures[future]
                extracted, error = future.result()
                results[i] = {"extracted": extracted, "error": error}
                done = sum(1 for r in results if r)
                status = f" — ERROR" if error else ""
                print(f"[{done}/{len(rows_to_process)}] Row {i + 1} complete{status}")
    else:
        for i, row in enumerate(rows_to_process):
            print(f"[{i + 1}/{len(rows_to_process)}] Processing...")
            extracted, error = _process_one_row(chain, row)
            results[i] = {"extracted": extracted, "error": error}
            if error:
                print(f"  Error: {error}")

    with dst_path.open("w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        for i, row in enumerate(rows_to_process):
            res = results[i]
            output_row = {
                "patient_id": f"{random.randint(1, 999999):06d}",
                "text": row["text"],
                "summary": row["summary"],
                **res["extracted"],
                "error": res["error"],
            }
            writer.writerow(output_row)

    processed = len(rows_to_process)
    print(f"\nDone. Processed {processed} row(s) → {dst_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch clinical intake extraction")
    parser.add_argument("src", type=str, help="Input CSV path")
    parser.add_argument("dst", type=str, help="Output CSV path")
    parser.add_argument("--limit", type=int, default=None, help="Max rows to process")
    parser.add_argument(
        "--concurrent",
        type=int,
        default=1,
        help="Parallel workers (default: 1 = sequential)",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="deepseek-v4-flash",
        help="LLM model (default: deepseek-v4-flash)",
    )
    args = parser.parse_args()

    process_csv(
        src=args.src,
        dst=args.dst,
        limit=args.limit,
        concurrent=args.concurrent,
        model=args.model,
    )
