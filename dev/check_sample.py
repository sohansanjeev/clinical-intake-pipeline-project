"""Quick inspection of sample.csv structure."""
import csv

with open("data/sample.csv", "r") as f:
    reader = csv.reader(f)
    header = next(reader)
    rows = [r for r in reader]

print(f"Header: {header}")
print(f"Actual row count: {len(rows)}")
print(f"First row text length: {len(rows[0][0]) if rows else 0} chars")
print(f"First row summary preview: {rows[0][1][:150] if rows else ''}")
print(f"Any empty text fields: {any(not r[0].strip() for r in rows)}")
print(f"Any empty summary fields: {any(not r[1].strip() for r in rows)}")
