"""Refresh postseason snapshots only when completed games or calculated data change."""
import argparse
import json
import os
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo

from mlb.client import MlbStatsClient
from mlb.postseason import aggregate_feeds
from scripts.refresh import ROOT, load_config, completed_games, build_roster_rows, public_payload
from scripts.publish_postseason import postseason_range


def meaningful(payload):
    return {key: value for key, value in payload.items() if key not in {"updated_at", "through", "through_date"}}


def refresh_if_needed(league, roster, client, today, audit=False, root=ROOT):
    if league.get("phase") != "postseason" or league.get("game_types") != "F,D,L,W":
        return False
    start, end = date.fromisoformat(league["start_date"]), date.fromisoformat(league["end_date"])
    # One extra day allows the final day's late games/corrections to be collected.
    if not start <= today <= end + timedelta(days=1):
        return False
    through = min(today, end).isoformat()
    league_path = root / "docs/data/league.json"
    stats_path = root / "docs/data/player-stats.json"
    old_league = json.loads(league_path.read_text(encoding="utf-8"))
    old_stats = json.loads(stats_path.read_text(encoding="utf-8"))
    old_post = next((row for row in old_stats["ranges"] if row["id"] == "postseason"), {})
    games = completed_games(client.schedule(start.isoformat(), through, "F,D,L,W"))
    ids = sorted({game["gamePk"] for game in games})
    if not audit and old_league.get("included_game_ids") == ids and old_post.get("included_game_ids") == ids:
        return False
    # Fetch fresh feeds: daily audits must see official scoring corrections.
    feeds = [client.live_game_feed(pk) for pk in ids]
    if any(feed.get("gameData", {}).get("status", {}).get("abstractGameState") != "Final" or
           not all(any(player.get("stats", {}).get(group)
                       for player in feed.get("liveData", {}).get("boxscore", {}).get("teams", {}).get(side, {}).get("players", {}).values())
                   for side in ("away", "home") for group in ("batting", "pitching")) for feed in feeds):
        raise ValueError("A completed game's feed is unavailable or no longer final; retaining saved data")
    pool = aggregate_feeds(feeds)
    new_league = public_payload(league, games, build_roster_rows(roster, pool))
    new_post = postseason_range(old_stats, league, pool, through)
    new_post["included_game_ids"] = ids
    changed_league = meaningful(old_league) != meaningful(new_league)
    changed_post = meaningful(old_post) != meaningful(new_post)
    # Do not rewrite timestamps or cutoff dates when nothing substantive changed.
    if changed_league:
        league_path.write_text(json.dumps(new_league, indent=2), encoding="utf-8")
    if changed_post:
        updated = old_stats | {"ranges": [new_post] + [row for row in old_stats["ranges"] if row["id"] != "postseason"]}
        stats_path.write_text(json.dumps(updated, indent=2), encoding="utf-8")
    return changed_league or changed_post


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true", help="check fresh box scores even without new completed games")
    args = parser.parse_args()
    league, roster = load_config()
    today = datetime.now(ZoneInfo("America/Los_Angeles")).date()
    changed = refresh_if_needed(league, roster, MlbStatsClient(), today, args.audit)
    print("Statistics changed." if changed else "No statistics changes; no deployment needed.")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as summary:
            summary.write("\n## Statistics result\n" + (
                "Updated statistics; publication will follow.\n" if changed else
                "No changes (or postseason date/phase gate inactive); deployment skipped.\n"))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write(f"changed={str(changed).lower()}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
