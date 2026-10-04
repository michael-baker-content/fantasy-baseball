"""Apply manual elimination status using the saved postseason player pool."""
import json

TEAM_CODES = dict(zip(
    ["Arizona Diamondbacks", "Atlanta Braves", "Baltimore Orioles", "Boston Red Sox",
     "Chicago Cubs", "Chicago White Sox", "Cincinnati Reds", "Cleveland Guardians",
     "Colorado Rockies", "Detroit Tigers", "Houston Astros", "Kansas City Royals",
     "Los Angeles Angels", "Los Angeles Dodgers", "Miami Marlins", "Milwaukee Brewers",
     "Minnesota Twins", "New York Mets", "New York Yankees", "Athletics",
     "Philadelphia Phillies", "Pittsburgh Pirates", "San Diego Padres", "San Francisco Giants",
     "Seattle Mariners", "St. Louis Cardinals", "Tampa Bay Rays", "Texas Rangers",
     "Toronto Blue Jays", "Washington Nationals"],
    "AZ ATL BAL BOS CHC CWS CIN CLE COL DET HOU KC LAA LAD MIA MIL MIN NYM NYY ATH PHI PIT SD SF SEA STL TB TEX TOR WSH".split(),
))


def eliminated_ids(league, root):
    eliminated = set(league.get("eliminated_teams", []))
    if not eliminated:
        return set()
    snapshot = json.loads((root / "docs/data/player-stats.json").read_text(encoding="utf-8"))
    ranges = snapshot.get("ranges", [])
    pool = next((r for r in ranges if r["id"] == "postseason"), None)
    if pool is None:
        pool = next((r for r in ranges if r["id"] == "ytd"), None)
    if pool is None:
        raise ValueError("Elimination status requires a saved postseason or YTD player pool")
    return {int(p["id"]) for group in ("batters", "pitchers") for p in pool.get(group, [])
            if (p.get("team_abbreviation") or TEAM_CODES.get(p.get("team"))) in eliminated}


def apply_eliminations(payload, league, root):
    ids = eliminated_ids(league, root)
    return payload | {
        "league": payload["league"] | {"eliminated_teams": league.get("eliminated_teams", [])},
        "owners": [owner | {"players": [player | {"eliminated": int(player["player_id"]) in ids}
                                        for player in owner["players"]]}
                   for owner in payload["owners"]],
    }
