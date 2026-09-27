"""Check a game's current MLB status and box-score availability without saving data."""

import argparse
import json
from pathlib import Path
from urllib.error import URLError

from mlb.client import MlbStatsClient
from scripts.verify_totals import verify_totals

ROOT = Path(__file__).resolve().parents[1]


def inclusion_status(snapshot, game_id):
    if snapshot is None:
        return "Unavailable: no saved snapshot"
    ids = snapshot.get("included_game_ids")
    if not isinstance(ids, list):
        return "Unknown: snapshot predates game tracking; run an update"
    return "Included" if str(game_id) in {str(value) for value in ids} else "Not included"


def postseason_report(game_id, root=ROOT):
    lines = ["Postseason inclusion in LOCAL saved totals:"]
    for label, filename in (("Standings / owner pages", "league.json"),
                            ("Postseason Player Stats", "player-stats.json")):
        path = root / "docs/data" / filename
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            snapshot = payload if filename == "league.json" else next(
                (row for row in payload.get("ranges", []) if row.get("id") == "postseason"), None)
            lines.append(f"  {label}: {inclusion_status(snapshot, game_id)}")
        except FileNotFoundError:
            lines.append(f"  {label}: Unavailable: no saved file")
        except (OSError, ValueError, TypeError, AttributeError) as error:
            lines.append(f"  {label}: Unable to read snapshot ({error})")
    lines.append("Included means the game was used in that calculation; only eligible roster/pool players contribute.")
    lines.append("This does not check the deployed website or later scoring corrections. Commit and push updated files to publish them.")
    return lines


def game_report(feed):
    game = feed.get("gameData", {})
    status = game.get("status", {})
    final = status.get("abstractGameState") == "Final"
    live = feed.get("liveData", {})
    boxes = live.get("boxscore", {}).get("teams", {})
    available = all(
        any(player.get("stats", {}).get(group)
            for player in boxes.get(side, {}).get("players", {}).values())
        for side in ("away", "home") for group in ("batting", "pitching")
    )
    teams = game.get("teams", {})
    matchup = " at ".join(teams.get(side, {}).get("name", side.title()) for side in ("away", "home"))
    lines = [matchup, f"Date: {game.get('datetime', {}).get('officialDate', 'Unknown')}",
             f"MLB status: {status.get('detailedState', status.get('abstractGameState', 'Unknown'))}",
             f"Game marked final: {'Yes' if final else 'No'}",
             f"Batting and pitching box scores for both teams: {'Available' if available else 'Incomplete or unavailable'}"]
    if final and available:
        lines.append("Final game with box scores available for a completed-game refresh.")
    else:
        lines.append("Not confirmed ready for a completed-game refresh. Check again later.")
    lines.append("MLB may make later scoring corrections.")
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game_id", type=int, help="numeric MLB gamePk")
    parser.add_argument("--verify-totals", action="store_true", help="compare regular-season daily totals with completed box scores")
    args = parser.parse_args()
    if args.game_id <= 0:
        parser.error("game_id must be positive")
    try:
        client = MlbStatsClient()
        feed = client.live_game_feed(args.game_id)
        if not feed.get("gameData", {}).get("status"):
            raise ValueError("MLB returned no game status; check the game ID")
    except (URLError, OSError, ValueError) as error:
        print(f"Could not check game {args.game_id}: {error}")
        return 1
    print(f"Game ID: {args.game_id}")
    print("\n".join(game_report(feed)))
    if args.verify_totals:
        try:
            print("\n" + "\n".join(verify_totals(client, args.game_id, feed)))
        except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
            print(f"Daily totals verification: Unable to verify ({error})")
            return 1
    elif feed.get("gameData", {}).get("game", {}).get("type") == "R":
        print("Not checked: regular-season daily totals. Add --verify-totals to compare them.")
    if feed.get("gameData", {}).get("game", {}).get("type") in {"F", "D", "L", "W"}:
        print("\n" + "\n".join(postseason_report(args.game_id)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
