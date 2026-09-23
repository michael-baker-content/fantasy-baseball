"""Publish manual Sheet selections without fetching MLB data."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def sheet_ids(path):
    selected, seen = [], set()
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"MLB ID", "Sheet"}.issubset(reader.fieldnames or []):
            raise ValueError("Sheet CSV requires MLB ID and Sheet columns")
        for row in reader:
            if row.get("MLB ID") is None or row.get("Sheet") is None or None in row:
                raise ValueError(f"Malformed Sheet CSV row {reader.line_num}")
            player_id = int(row["MLB ID"])
            choice = row["Sheet"].strip().casefold()
            if player_id <= 0 or player_id in seen or choice not in {"yes", "no"}:
                raise ValueError(f"Invalid or duplicate Sheet entry: {player_id}")
            seen.add(player_id)
            if choice == "yes":
                selected.append(player_id)
    return sorted(selected)


def main():
    ids = sheet_ids(ROOT / "config/sheet-players.csv")
    output = ROOT / "docs/data/sheet-players.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps({"player_ids": ids}, indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    print(f"Published {len(ids)} Sheet players.")


if __name__ == "__main__":
    main()
