"""Rebuild the 2025 BABBD postseason results from official MLB box scores."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from config.mlb_roster_2025 import EXPECTED_TOTALS_2025, PLAYER_ID_OVERRIDES_2025, ROSTER_2025
from mlb.client import MlbStatsClient
from mlb.postseason import aggregate_feeds, candidate_players, player_output
from mlb.scoring import owner_totals, roto_standings


def completed_game_ids(schedule: dict) -> list[int]:
    return [
        game["gamePk"]
        for date in schedule.get("dates", [])
        for game in date.get("games", [])
        if game.get("status", {}).get("abstractGameState") == "Final"
    ]


def resolve_roster(players: dict[int, dict]) -> tuple[list[dict], list[dict]]:
    resolved, problems = [], []
    for owner, sections in ROSTER_2025.items():
        for section, entries in sections.items():
            for slot, label in entries:
                key = (owner, section, label)
                override = PLAYER_ID_OVERRIDES_2025.get(key)
                candidates = candidate_players(label, players, section)
                if override:
                    selected = players.get(override)
                else:
                    with_stats = [row for row in candidates if row["has_stats"]]
                    selected = players.get(with_stats[0]["player_id"]) if len(with_stats) == 1 else None
                if not selected:
                    problems.append({"owner": owner, "section": section, "slot": slot,
                                     "label": label, "candidates": candidates})
                    continue
                resolved.append({"owner": owner, "section": section, "slot": slot, "label": label,
                                 "player_id": selected["player_id"], "player_name": selected["name"],
                                 "stats": player_output(selected, section)})
    return resolved, problems


def reconciliation(totals: dict[str, dict]) -> list[dict]:
    rows = []
    for owner, expected in EXPECTED_TOTALS_2025.items():
        actual = totals[owner]
        for category, expected_value in expected.items():
            actual_value = actual[category]
            # The workbook stores innings as decimal approximations (for example
            # 6.667 for 6 2/3). MLB supplies baseball notation, so rebuilding via
            # exact outs produces tiny, harmless rate differences.
            tolerance = 1e-4 if category in {"ERA", "WHIP"} else (1e-8 if category == "AVG" else 0)
            rows.append({"owner": owner, "category": category, "expected": expected_value,
                         "actual": actual_value, "difference": actual_value - expected_value,
                         "matches": abs(actual_value - expected_value) <= tolerance})
    return rows


def write_outputs(output_dir: Path, players: list[dict], totals: dict, standings: list[dict], checks: list[dict]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    payloads = {"players.json": players, "owner_totals.json": totals, "standings_5x5.json": standings,
                "reconciliation.json": checks}
    for filename, payload in payloads.items():
        (output_dir / filename).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    with (output_dir / "reconciliation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("owner", "category", "expected", "actual", "difference", "matches"))
        writer.writeheader()
        writer.writerows(checks)
    flat_player_rows = []
    for row in players:
        flat_player_rows.append({key: value for key, value in row.items() if key != "stats"} | row["stats"])
    leading = ["owner", "section", "slot", "label", "player_id", "player_name"]
    fieldnames = leading + sorted({key for row in flat_player_rows for key in row} - set(leading))
    with (output_dir / "players.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(flat_player_rows)
    with (output_dir / "owner_totals.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["owner"] + list(next(iter(totals.values())))
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({"owner": owner} | values for owner, values in totals.items())
    with (output_dir / "standings_5x5.csv").open("w", newline="", encoding="utf-8") as handle:
        categories = ("R", "HR", "RBI", "SB", "AVG", "W", "SV", "K", "ERA", "WHIP")
        fieldnames = ["place", "owner", "total_score"] + [f"{key}_points" for key in categories]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({"place": row["place"], "owner": row["owner"], "total_score": row["total_score"]}
                         | {f"{key}_points": row["category_points"][key] for key in categories}
                         for row in standings)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="redownload cached game feeds")
    parser.add_argument("--output", default="data/2025", help="output directory")
    args = parser.parse_args()

    client = MlbStatsClient()
    game_ids = completed_game_ids(client.postseason_schedule(2025))
    print(f"Fetching {len(game_ids)} completed 2025 postseason games...")
    pool = aggregate_feeds([client.game_feed(game_id, refresh=args.refresh) for game_id in game_ids])
    roster, problems = resolve_roster(pool)
    if problems:
        print(json.dumps({"unresolved": problems}, indent=2))
        return 2
    totals = owner_totals(roster)
    standings = roto_standings(totals)
    checks = reconciliation(totals)
    write_outputs(Path(args.output), roster, totals, standings, checks)
    matched = sum(row["matches"] for row in checks)
    print(f"Resolved {len(roster)} roster entries; matched {matched}/{len(checks)} reference totals.")
    return 0 if matched == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
