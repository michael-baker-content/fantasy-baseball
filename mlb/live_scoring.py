"""Appearance-aware scoring for the live postseason league."""
from mlb.scoring import owner_totals, roto_standings, scoring_categories


def live_results(league, rows):
    totals = owner_totals(rows, league["owners"])
    categories = scoring_categories(league["categories"])
    hitting = set(league["categories"]["hitting"])
    appearances = {owner: {section: any(
        row["owner"] == owner and row["section"] == section and (row["stats"].get("G") or 0) > 0
        for row in rows) for section in ("hitting", "pitching")} for owner in league["owners"]}
    points = {owner: {} for owner in totals}
    for category, lower in categories:
        section = "hitting" if category in hitting else "pitching"
        eligible = {owner: stats for owner, stats in totals.items() if appearances[owner][section] and
                    (category != "AVG" or stats["AB"] > 0) and
                    (category not in {"ERA", "WHIP"} or stats["P_OUTS"] > 0)}
        ranked = roto_standings(eligible, [(category, lower)])
        offset = len(totals) - len(eligible)
        for owner in totals:
            points[owner][category] = None
        for standing in ranked:
            points[standing["owner"]][category] = standing["category_points"][category] + offset
    for owner, stats in totals.items():
        if not appearances[owner]["hitting"]:
            for key in ("R", "HR", "RBI", "SB", "BB", "AVG", "H", "AB"):
                stats[key] = None
        elif not stats["AB"]:
            stats["AVG"] = None
        if not appearances[owner]["pitching"]:
            for key in ("W", "L", "SV", "K", "ERA", "WHIP", "IP", "P_H", "P_BB", "P_ER", "P_OUTS"):
                stats[key] = None
        elif not stats["P_OUTS"]:
            stats["ERA"] = stats["WHIP"] = None
    standings = []
    for owner, stats in totals.items():
        active = any(appearances[owner].values())
        standings.append({"owner": owner, "stats": stats, "category_points": points[owner],
                          "total_score": sum(v for v in points[owner].values() if v is not None) if active else None})
    standings.sort(key=lambda row: (row["total_score"] is None, -(row["total_score"] or 0), row["owner"]))
    for index, standing in enumerate(standings):
        standing["place"] = standings[index-1]["place"] if index and standing["total_score"] == standings[index-1]["total_score"] else index + 1
    return totals, standings


def appearance_stats(stats, section):
    if not stats.get("G"):
        return {key: None for key in stats}
    result = dict(stats)
    if section == "hitting" and not stats.get("AB"):
        result["AVG"] = None
    if section == "pitching" and not stats.get("OUTS"):
        result["ERA"] = result["WHIP"] = None
    return result
