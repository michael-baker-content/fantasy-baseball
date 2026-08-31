"""Aggregate official MLB postseason box scores and resolve drafted players."""

from __future__ import annotations

import re
import unicodedata
from collections import defaultdict


HITTING_FIELDS = ("gamesPlayed", "atBats", "runs", "hits", "doubles", "triples", "homeRuns",
                  "rbi", "baseOnBalls", "strikeOuts", "stolenBases", "caughtStealing")
PITCHING_FIELDS = ("gamesPlayed", "gamesStarted", "hits", "runs", "earnedRuns", "homeRuns",
                   "hitByPitch", "baseOnBalls", "strikeOuts", "saveOpportunities")


def _empty_player(player_id: int, name: str) -> dict:
    return {
        "player_id": player_id, "name": name,
        "hitting": defaultdict(int), "pitching": defaultdict(int), "pitching_outs": 0,
    }


def innings_to_outs(value: str) -> int:
    whole, _, partial = str(value or "0.0").partition(".")
    return int(whole) * 3 + int(partial or 0)


def aggregate_feeds(feeds: list[dict]) -> dict[int, dict]:
    players: dict[int, dict] = {}
    for feed in feeds:
        boxscore = feed.get("liveData", {}).get("boxscore", {})
        for side in ("away", "home"):
            team = boxscore.get("teams", {}).get(side, {})
            for raw in team.get("players", {}).values():
                person = raw.get("person", {})
                player_id = person.get("id")
                if not player_id:
                    continue
                player = players.setdefault(player_id, _empty_player(player_id, person.get("fullName", "")))
                batting = raw.get("stats", {}).get("batting", {})
                pitching = raw.get("stats", {}).get("pitching", {})
                for field in HITTING_FIELDS:
                    player["hitting"][field] += int(batting.get(field, 0) or 0)
                for field in PITCHING_FIELDS:
                    player["pitching"][field] += int(pitching.get(field, 0) or 0)
                player["pitching_outs"] += innings_to_outs(pitching.get("inningsPitched", "0.0"))

        decisions = feed.get("liveData", {}).get("decisions", {})
        for decision, field in (("winner", "wins"), ("loser", "losses"), ("save", "saves")):
            person = decisions.get(decision)
            if person and person.get("id"):
                player = players.setdefault(person["id"], _empty_player(person["id"], person.get("fullName", "")))
                player["pitching"][field] += 1
    return players


def normalized(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", ascii_value)


def candidate_players(label: str, players: dict[int, dict], section: str) -> list[dict]:
    wanted = normalized(label)
    candidates = []
    for player in players.values():
        full = normalized(player["name"])
        last = normalized(player["name"].split()[-1])
        initials_last = normalized("".join(part[0] for part in player["name"].split()[:-1]) + player["name"].split()[-1])
        has_stats = (sum(player[section].values()) > 0 or (section == "pitching" and player["pitching_outs"] > 0))
        if wanted in {full, last, initials_last} or full.endswith(wanted):
            candidates.append({"player_id": player["player_id"], "name": player["name"], "has_stats": has_stats})
    return sorted(candidates, key=lambda row: (not row["has_stats"], row["name"]))


def player_output(player: dict, section: str) -> dict:
    if section == "hitting":
        s = player["hitting"]
        return {
            "G": s["gamesPlayed"], "AB": s["atBats"], "R": s["runs"], "H": s["hits"],
            "2B": s["doubles"], "3B": s["triples"], "HR": s["homeRuns"], "RBI": s["rbi"],
            "BB": s["baseOnBalls"], "SO": s["strikeOuts"], "SB": s["stolenBases"],
            "CS": s["caughtStealing"], "AVG": s["hits"] / s["atBats"] if s["atBats"] else 0,
        }
    s = player["pitching"]
    outs = player["pitching_outs"]
    innings = outs / 3
    return {
        "W": s["wins"], "L": s["losses"], "SV": s["saves"], "K": s["strikeOuts"],
        "G": s["gamesPlayed"], "GS": s["gamesStarted"], "H": s["hits"], "R": s["runs"],
        "ER": s["earnedRuns"], "HR": s["homeRuns"], "HB": s["hitByPitch"], "BB": s["baseOnBalls"],
        "OUTS": outs, "IP": f"{outs // 3}.{outs % 3}",
        "ERA": (s["earnedRuns"] * 9 / innings) if innings else 0,
        "WHIP": ((s["hits"] + s["baseOnBalls"]) / innings) if innings else 0,
    }
