"""
Batch CSV processor — runs the extraction pipeline over every row in a CSV.

Reads a CSV with 'text' and 'summary' columns, runs the extraction chain
on each note, and writes the results to an output CSV with the original
columns plus all extracted fields flattened into new columns.

Usage:
    python -m pipeline data/sample.csv data/output.csv
"""

from pathlib import Path
from typing import Optional

from clinical_intake.chain import run_extraction


def process_csv(
    src: str | Path,
    dst: str | Path,
    *,
    limit: Optional[int] = None,
    model: str = "deepseek-chat",
    base_url: str = "https://api.deepseek.com/v1",
    api_key: Optional[str] = None,
) -> None:
    """Read a CSV of notes, extract intake data, write annotated CSV.

    Args:
        src: Path to input CSV (must have 'text' and 'summary' columns).
        dst: Path to output CSV (original columns + extracted fields).
        limit: Optional max rows to process (for testing).
        model: LLM model name.
        base_url: API base URL.
        api_key: API key (falls back to DEEPSEEK_API_KEY env var).
    """
    ...


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Batch clinical intake extraction")
    parser.add_argument("src", type=str, help="Input CSV path")
    parser.add_argument("dst", type=str, help="Output CSV path")
    parser.add_argument("--limit", type=int, default=None, help="Max rows to process")
    parser.add_argument("--model", type=str, default="deepseek-chat", help="LLM model")
    args = parser.parse_args()

    process_csv(
        src=args.src,
        dst=args.dst,
        limit=args.limit,
        model=args.model,
    )
