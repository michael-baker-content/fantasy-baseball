"""Read-only comparison of completed box scores with regular-season daily totals."""
from datetime import date

from mlb.postseason import innings_to_outs
from scripts.export_mlb_ytd import season_splits, combined_splits

FIELDS = {
    "hitting": ("atBats", "hits", "runs", "homeRuns", "rbi", "stolenBases", "baseOnBalls"),
    "pitching": ("inningsPitched", "hits", "earnedRuns", "baseOnBalls", "strikeOuts"),
}


def count(field, value):
    if value is None or value == "":
        raise ValueError(f"Missing {field}")
    return innings_to_outs(value) if field == "inningsPitched" else int(value)


def verify_totals(client, game_id, feed):
    """Return a human-readable result; never write snapshots or game caches."""
    game = feed["gameData"]
    if game.get("game", {}).get("type") != "R":
        return ["Daily totals verification: Not applicable (regular-season games only).",
                "Postseason uses box scores directly; see local snapshot inclusion below."]
    if game.get("status", {}).get("abstractGameState") != "Final":
        return ["Daily totals verification: Unable to verify; the game is not final."]
    day = game["datetime"]["officialDate"]
    season = date.fromisoformat(day).year
    team_ids = {game["teams"][side]["id"] for side in ("away", "home")}
    scheduled = client.schedule(day, day, "R")
    games = {row["gamePk"]: row for block in scheduled.get("dates", []) for row in block.get("games", [])
             if row.get("officialDate") == day and any(
                 row.get("teams", {}).get(side, {}).get("team", {}).get("id") in team_ids
                 for side in ("away", "home"))}
    if game_id not in games:
        raise ValueError("The target game is missing from its official-date schedule")
    if any(row.get("status", {}).get("abstractGameState") != "Final" for row in games.values()):
        return ["Daily totals verification: Unable to verify; another game for these teams on this date is not final (including postponed or suspended games)."]
    expected = {group: {} for group in FIELDS}
    names = {}
    for pk in games:
        current = feed if pk == game_id else client.live_game_feed(pk)
        if current.get("gameData", {}).get("status", {}).get("abstractGameState") != "Final":
            raise ValueError(f"Game {pk} is not final in its live feed")
        for side in ("away", "home"):
            players = current.get("liveData", {}).get("boxscore", {}).get("teams", {}).get(side, {}).get("players", {})
            for group, fields in FIELDS.items():
                found = False
                for player in players.values():
                    stats = player.get("stats", {}).get("batting" if group == "hitting" else "pitching")
                    if not stats:
                        continue
                    # A nonempty stat line alone is not an offensive appearance.
                    if group == "hitting" and not any(stats.get(key, 0) for key in ("plateAppearances", "atBats", "runs", "stolenBases", "baseOnBalls")):
                        continue
                    found = True
                    pid = player["person"]["id"]
                    names[pid] = player["person"].get("fullName", str(pid))
                    totals = expected[group].setdefault(pid, dict.fromkeys(fields, 0))
                    for field in fields:
                        totals[field] += count(field, stats.get(field))
                if not found:
                    raise ValueError(f"Game {pk} lacks {side} {group} box-score data")
    differences = []
    for group, players in expected.items():
        splits = combined_splits(season_splits(group, season, day, day), group, season, day, day, set(players))
        actual = {row["player"]["id"]: row["stat"] for row in splits}
        for pid, totals in players.items():
            if pid not in actual:
                differences.append(f"{names[pid]} ({group}): daily totals row missing")
                continue
            for field, wanted in totals.items():
                value = count(field, actual[pid].get(field))
                if value != wanted:
                    unit = "outs" if field == "inningsPitched" else field
                    differences.append(f"{names[pid]} ({group}) {unit}: box scores {wanted}, daily totals {value}")
    result = [f"Daily totals verification: {'Totals not yet matching' if differences else 'Daily totals match'}.",
              f"Checked {len(games)} completed game(s) for these teams on {day}; doubleheaders are combined."]
    result.extend(differences[:15])
    if len(differences) > 15:
        result.append(f"...and {len(differences) - 15} more differences.")
    result.append("Checks AB, H, R, HR, RBI, SB, BB and pitching outs, H, ER, BB, K. Does not check W/L/SV or every statistic.")
    result.append("This checks one-day API totals, not the saved website or every season-long query. Differences may reflect processing delays or scoring corrections.")
    return result
