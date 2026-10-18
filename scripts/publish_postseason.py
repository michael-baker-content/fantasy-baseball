"""Publish completed-game postseason stats for the saved regular-season player pool."""
import argparse
import json
from datetime import date, timedelta
from scripts.refresh import ROOT, load_config, completed_games, build_roster_rows
from mlb.client import MlbStatsClient
from mlb.postseason import aggregate_feeds
from mlb.live_scoring import appearance_stats


def postseason_range(payload, league, pool, through):
    source = next(row for row in payload["ranges"] if row["id"] == "ytd" and row["season"] == league["season"])
    entry = {key: source[key] for key in ("season", "teams", "roster_date")}
    entry.update(id="postseason", label="Postseason", start=league["start_date"], through=through)
    for group, section in (("batters", "hitting"), ("pitchers", "pitching")):
        entry[group] = []
        for player in source[group]:
            roster = [{"player_id": player["id"], "player_name": player["name"], "section": section}]
            stats = appearance_stats(build_roster_rows(roster, pool)[0]["stats"], section)
            entry[group].append(player | {"stats": stats})
    return entry


def postseason_last7_range(payload, league, games, feeds, through):
    start = max(league["start_date"], (date.fromisoformat(through) - timedelta(days=6)).isoformat())
    selected = [(game, feed) for game, feed in zip(games, feeds)
                if start <= game["officialDate"] <= through]
    entry = postseason_range(payload, league, aggregate_feeds([feed for _, feed in selected]), through)
    entry.update(id="postseason-last7", label="Last 7 Days - Postseason", start=start,
                 included_game_ids=sorted({game["gamePk"] for game, _ in selected}))
    return entry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--through", default=date.today().isoformat())
    args = parser.parse_args()
    date.fromisoformat(args.through)
    league, _ = load_config()
    through = min(args.through, league["end_date"])
    path = ROOT / "docs/data/player-stats.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    client = MlbStatsClient(ROOT / "data/mlb_cache")
    games = completed_games(client.schedule(league["start_date"], through, "F,D,L,W"), league["start_date"], through) if through >= league["start_date"] else []
    feeds = [client.game_feed(game["gamePk"]) for game in games]
    pool = aggregate_feeds(feeds)
    entry = postseason_range(payload, league, pool, through)
    entry["included_game_ids"] = sorted({game["gamePk"] for game in games})
    recent = postseason_last7_range(payload, league, games, feeds, through)
    payload["ranges"] = [entry, recent] + [row for row in payload["ranges"] if row["id"] not in {"postseason", "postseason-last7"}]
    for row in payload["ranges"]:
        if row["id"] == "last30":
            row["label"] = "Last 30 Days - Regular Season"
        elif row["id"] == "ytd":
            row["label"] = f"{row['season']} Regular Season"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Updated postseason Player Stats using {len(games)} completed games.")


if __name__ == "__main__":
    main()
