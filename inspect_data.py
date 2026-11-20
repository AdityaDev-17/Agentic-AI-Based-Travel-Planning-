"""Prints the structure of each JSON dataset so tools can be designed against real schemas."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
FILES = ["flights.json", "hotels.json", "places.json"]
HINT_WORDS = ("city", "source", "destination", "from", "to", "type", "category")


def find_records(raw):
    """Return the list of records, unwrapping a dict that holds a list."""
    if isinstance(raw, list):
        return raw
    for value in raw.values():
        if isinstance(value, list):
            return value
    return [raw]


def inspect_file(filename):
    path = DATA_DIR / filename
    try:
        with open(path, encoding="utf-8") as file:
            raw = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as error:
        print(f"\n=== {filename} === FAILED: {error}")
        return

    records = find_records(raw)
    print(f"\n=== {filename} ===")
    print("Top-level type:", type(raw).__name__)
    if isinstance(raw, dict):
        print("Top-level keys:", list(raw.keys()))
    print("Record count:", len(records))
    print("Sample record:")
    print(json.dumps(records[0], indent=2, ensure_ascii=False))

    for key in records[0]:
        if any(word in key.lower() for word in HINT_WORDS):
            unique = sorted({str(r.get(key)) for r in records})
            print(f"Unique '{key}' ({len(unique)}):", unique[:25])


if __name__ == "__main__":
    for name in FILES:
        inspect_file(name)