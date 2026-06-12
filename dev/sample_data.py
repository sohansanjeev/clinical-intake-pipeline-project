"""Utility: sample the first N rows from mimic_data.csv."""

import csv
from pathlib import Path


def create_sample(n: int = 20, src: str | Path = "data/mimic_data.csv",
                  dst: str | Path = "data/sample.csv") -> None:
    """Read first N data rows from src CSV and write to dst, preserving the header."""
    src_path = Path(src)
    dst_path = Path(dst)

    # Ensure output directory exists
    dst_path.parent.mkdir(parents=True, exist_ok=True)

    with src_path.open("r", newline="", encoding="utf-8") as fin:
        reader = csv.reader(fin)
        header = next(reader)
        rows = [next(reader) for _ in range(n)]

    with dst_path.open("w", newline="", encoding="utf-8") as fout:
        writer = csv.writer(fout)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"Wrote {n} rows to {dst_path}")


if __name__ == "__main__":
    create_sample()
