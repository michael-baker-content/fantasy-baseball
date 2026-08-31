"""Refresh the static BABBD site with MLB games in the configured league window."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

from mlb.client import MlbStatsClient
from mlb.postseason import aggregate_feeds, player_output
from mlb.scoring import owner_totals, roto_standings


ROOT = Path(__file__).resolve().parent


def load_config() -> tuple[dict, list[dict]]:
    league = json.loads((ROOT / "config/league.json").read_text(encoding="utf-8"))
    with (ROOT / "config/roster.csv").open(encoding="utf-8-sig", newline="") as handle:
        roster = list(csv.DictReader(handle))
    for row in roster:
        row["player_id"] = int(row["player_id"])
    return league, roster


def completed_games(schedule: dict) -> list[dict]:
    return [
        game
        for day in schedule.get("dates", [])
        for game in day.get("games", [])
        if game.get("status", {}).get("abstractGameState") == "Final"
    ]


def build_roster_rows(roster: list[dict], pool: dict[int, dict]) -> list[dict]:
    rows = []
    for entry in roster:
        player = pool.get(entry["player_id"], {
            "player_id": entry["player_id"], "name": entry["player_name"],
            "hitting": defaultdict(int), "pitching": defaultdict(int), "pitching_outs": 0,
        })
        rows.append(entry | {"stats": player_output(player, entry["section"])})
    return rows


def public_payload(league: dict, games: list[dict], rows: list[dict]) -> dict:
    totals = owner_totals(rows)
    standings = roto_standings(totals)
    owners = []
    for owner in league["owners"]:
        owners.append({
            "name": owner,
            "players": [row for row in rows if row["owner"] == owner],
            "totals": totals[owner],
        })
    latest_game_date = max((game["officialDate"] for game in games), default=None)
    return {
        "league": league,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "through_date": latest_game_date,
        "games_counted": len(games),
        "standings": standings,
        "owners": owners,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--through", help="last date to consider, YYYY-MM-DD (defaults to today)")
    parser.add_argument("--refresh", action="store_true", help="redownload cached final game feeds")
    args = parser.parse_args()
    league, roster = load_config()
    requested = args.through or date.today().isoformat()
    through = min(max(requested, league["start_date"]), league["end_date"])
    client = MlbStatsClient(ROOT / "data/mlb_cache")
    schedule = client.schedule(league["start_date"], through, league["game_types"])
    games = completed_games(schedule)
    print(f"Found {len(games)} completed game(s) from {league['start_date']} through {through}.")
    pool = aggregate_feeds([client.game_feed(game["gamePk"], refresh=args.refresh) for game in games])
    rows = build_roster_rows(roster, pool)
    payload = public_payload(league, games, rows)
    output = ROOT / "docs/data/league.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Updated {output.relative_to(ROOT)} with {len(rows)} roster entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
