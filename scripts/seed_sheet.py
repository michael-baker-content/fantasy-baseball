"""Make a one-time draft-sheet first pass from saved YTD statistics."""

import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path

from scripts.build_sheet import FIELDS, ROOT, build_rows


def value(stats, key):
    return float(stats.get(key) or 0)


def draft_score(player, group):
    stats = player["stats"]
    if group == "batters":
        return (value(stats, "AB") + 8 * value(stats, "HR")
                + 12 * value(stats, "SB") + value(stats, "R")
                + value(stats, "RBI") + value(stats, "BB"))
    whole, _, outs = str(stats.get("IP") or "0").partition(".")
    innings = int(whole) + int(outs or 0) / 3
    return innings + 0.5 * value(stats, "K") + 12 * value(stats, "SV") + 5 * value(stats, "W")


def select_players(payload):
    ytd = next(item for item in payload["ranges"] if item["id"] == "ytd")
    selected = set()
    counts = {}
    for group, limit in (("batters", 11), ("pitchers", 8)):
        teams = defaultdict(dict)
        for player in ytd[group]:
            # Exclude position players' incidental pitching appearances.
            if group == "pitchers" and player.get("position", "").upper() not in {"P", "SP", "RP", "TWP"}:
                continue
            teams[player["team"]][str(player["id"])] = player
        for team in ytd["teams"]:
            ranked = sorted(teams[team].values(),
                            key=lambda player: (-draft_score(player, group), player["name"], str(player["id"])))
            picks = ranked[:limit]
            selected.update(str(player["id"]) for player in picks)
            counts[team, group] = len(picks)
    return selected, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "config/sheet-players.csv",
                        help="new CSV path; existing files are never overwritten")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists. Use --output config/sheet-suggestions.csv to keep your current review.")
    payload = json.loads((ROOT / "docs/data/player-stats.json").read_text(encoding="utf-8"))
    selected, counts = select_players(payload)
    rows = build_rows(payload, {player_id: "Yes" for player_id in selected})
    with args.output.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    for team in sorted({team for team, _ in counts}):
        print(f"{team}: {counts[team, 'batters']} hitters, {counts[team, 'pitchers']} pitchers")
    print(f"Wrote {len(rows)} players ({len(selected)} Yes) to {args.output}")
    print("Heuristic only: review injuries and expected postseason roles. No MLB data downloaded.")


if __name__ == "__main__":
    main()
