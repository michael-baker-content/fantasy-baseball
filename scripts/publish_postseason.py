"""Publish completed-game postseason stats for the saved regular-season player pool."""
import argparse
import json
from datetime import date
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
    games = completed_games(client.schedule(league["start_date"], through, "F,D,L,W")) if through >= league["start_date"] else []
    pool = aggregate_feeds([client.game_feed(game["gamePk"]) for game in games])
    entry = postseason_range(payload, league, pool, through)
    payload["ranges"] = [entry] + [row for row in payload["ranges"] if row["id"] != "postseason"]
    for row in payload["ranges"]:
        if row["id"] == "last30":
            row["label"] = "Last 30 Days - Regular Season"
        elif row["id"] == "ytd":
            row["label"] = f"{row['season']} Regular Season"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Updated postseason Player Stats using {len(games)} completed games.")


if __name__ == "__main__":
    main()
