"""Build the offline draft-review CSV from the saved YTD player pool."""

import csv
import json
from pathlib import Path
import unicodedata

ROOT = Path(__file__).resolve().parent
FIELDS = ["League", "Team", "Last Name", "First Name", "MLB ID", "Sheet"]
AL_TEAMS = {"Boston Red Sox", "Chicago White Sox", "Cleveland Guardians",
            "Houston Astros", "New York Yankees", "Tampa Bay Rays", "Texas Rangers"}
NL_TEAMS = {"Arizona Diamondbacks", "Atlanta Braves", "Chicago Cubs",
            "Los Angeles Dodgers", "Milwaukee Brewers", "Philadelphia Phillies", "San Diego Padres"}


def sort_text(value):
    return "".join(c for c in unicodedata.normalize("NFD", value.casefold())
                   if not unicodedata.combining(c))


def build_rows(payload, previous):
    ytd = next(item for item in payload["ranges"] if item["id"] == "ytd")
    players = {str(player["id"]): player for player in [*ytd["batters"], *ytd["pitchers"]]}
    rows = []
    for player_id, player in players.items():
        team = player["team"]
        if team not in AL_TEAMS | NL_TEAMS:
            raise ValueError(f"Unknown league for {team}; update the team mapping first.")
        # Published display names use a given name followed by the full surname,
        # including particles (De La Cruz) and suffixes (Jr., II, III).
        first, last = player["name"].split(" ", 1)
        rows.append({"League": "AL" if team in AL_TEAMS else "NL", "Team": team,
                     "Last Name": last, "First Name": first, "MLB ID": player_id,
                     "Sheet": previous.get(player_id, "No")})
    return sorted(rows, key=lambda row: tuple(sort_text(row[key]) for key in FIELDS[:4]))


def main():
    output = ROOT / "config/sheet-players.csv"
    previous = {}
    if output.exists():
        with output.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                player_id = str(int(row["MLB ID"]))
                value = row["Sheet"].strip().capitalize()
                if value not in {"Yes", "No"} or player_id in previous:
                    raise ValueError(f"Invalid Sheet value or duplicate MLB ID: {player_id}")
                previous[player_id] = value
    payload = json.loads((ROOT / "docs/data/player-stats.json").read_text(encoding="utf-8"))
    rows = build_rows(payload, previous)
    # Preserve the earlier review before replacing it, including departed players.
    if output.exists():
        output.with_suffix(".csv.bak").write_bytes(output.read_bytes())
    temporary = output.with_suffix(".csv.tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(output)
    print(f"Wrote {len(rows)} unique players to {output.relative_to(ROOT)}. Edit Sheet to Yes or No.")


if __name__ == "__main__":
    main()
