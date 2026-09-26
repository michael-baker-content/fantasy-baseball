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
from mlb.scoring import owner_totals, roto_standings, scoring_categories


ROOT = Path(__file__).resolve().parents[1]


def validate_config(league: dict, roster: list[dict]) -> None:
    owners = league.get("owners")
    if not isinstance(owners, list) or not owners or any(
        not isinstance(name, str) or not name.strip() or name != name.strip() for name in owners
    ):
        raise ValueError("config/league.json: owners must be a nonempty list of names without surrounding spaces")
    if len({name.casefold() for name in owners}) != len(owners):
        raise ValueError("config/league.json: owner names must be unique (ignoring case)")
    scoring_categories(league["categories"])
    seen = set()
    for line, row in enumerate(roster, 2):
        if row.get("owner") not in owners:
            raise ValueError(f"config/roster.csv row {line}: unknown owner {row.get('owner')!r}; match config/league.json")
        if row.get("section") not in {"hitting", "pitching"}:
            raise ValueError(f"config/roster.csv row {line}: section must be hitting or pitching")
        if not str(row.get("player_id", "")).isdigit() or int(row["player_id"]) <= 0:
            raise ValueError(f"config/roster.csv row {line}: player_id must be a positive MLB ID")
        if any(not str(row.get(key) or "").strip() for key in ("slot", "player_name")):
            raise ValueError(f"config/roster.csv row {line}: slot and player_name are required")
        key = (row["owner"], row["section"], int(row["player_id"]))
        if key in seen:
            raise ValueError(f"config/roster.csv row {line}: duplicate player in the same owner's section")
        seen.add(key)


def load_config() -> tuple[dict, list[dict]]:
    league = json.loads((ROOT / "config/league.json").read_text(encoding="utf-8"))
    with (ROOT / "config/roster.csv").open(encoding="utf-8-sig", newline="") as handle:
        roster = list(csv.DictReader(handle))
    validate_config(league, roster)
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
    totals = owner_totals(rows, league["owners"])
    standings = roto_standings(totals, scoring_categories(league["categories"]))
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


def recalculate_payload(payload: dict, categories: dict) -> dict:
    """Re-score the saved player stats without fetching games or changing dates."""
    rows = [row for owner in payload["owners"] for row in owner["players"]]
    totals = owner_totals(rows, payload["league"]["owners"])
    return payload | {
        "league": payload["league"] | {"categories": categories},
        "standings": roto_standings(totals, scoring_categories(categories)),
        "owners": [owner | {"totals": totals[owner["name"]]} for owner in payload["owners"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--through", help="last date to consider, YYYY-MM-DD (defaults to today)")
    parser.add_argument("--refresh", action="store_true", help="redownload cached final game feeds")
    parser.add_argument("--check-config", action="store_true", help="validate owners and rosters offline without changing files")
    parser.add_argument("--recalculate", action="store_true",
                        help="re-score the existing site snapshot offline; do not download MLB data")
    args = parser.parse_args()
    if args.recalculate and (args.through or args.refresh):
        parser.error("--recalculate cannot be combined with --through or --refresh")
    if args.check_config and (args.through or args.refresh or args.recalculate):
        parser.error("--check-config cannot be combined with refresh options")
    try:
        league, roster = load_config()
    except (ValueError, KeyError) as error:
        parser.error(str(error))
    if args.check_config:
        print(f"Valid configuration: {len(league['owners'])} owners, {len(roster)} roster entries.")
        for owner in league["owners"]:
            print(f"  {owner}: {sum(row['owner'] == owner for row in roster)} entries")
        return 0
    if args.recalculate:
        output = ROOT / "docs/data/league.json"
        payload = json.loads(output.read_text(encoding="utf-8"))
        roster_keys = ("owner", "section", "slot", "player_id", "player_name")
        saved_rows = [row for owner in payload["owners"] for row in owner["players"]]
        signature = lambda entries: sorted(tuple(row[key] for key in roster_keys) for row in entries)
        if payload["league"]["owners"] != league["owners"] or signature(saved_rows) != signature(roster):
            parser.error("Owners or rosters changed. Run .\\update.cmd or a normal refresh; --recalculate uses saved rosters.")
        payload = recalculate_payload(payload, league["categories"])
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"Recalculated {output.relative_to(ROOT)} using saved stats; no MLB data downloaded.")
        return 0
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
