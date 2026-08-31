"""Aggregate roster totals and calculate rotisserie ranks."""

from __future__ import annotations


COUNTING_HITTING = ("R", "HR", "RBI", "SB", "BB")
COUNTING_PITCHING = ("W", "L", "SV", "K")
ROTO_5X5 = (("R", False), ("HR", False), ("RBI", False), ("SB", False), ("AVG", False),
            ("W", False), ("SV", False), ("K", False), ("ERA", True), ("WHIP", True))


def owner_totals(rows: list[dict]) -> dict[str, dict]:
    owners: dict[str, dict] = {}
    for row in rows:
        total = owners.setdefault(row["owner"], {key: 0 for key in (*COUNTING_HITTING, *COUNTING_PITCHING)})
        stats = row["stats"]
        if row["section"] == "hitting":
            for key in COUNTING_HITTING:
                total[key] += stats[key]
            total["H"] = total.get("H", 0) + stats["H"]
            total["AB"] = total.get("AB", 0) + stats["AB"]
        else:
            for key in COUNTING_PITCHING:
                total[key] += stats[key]
            for key in ("H", "BB", "ER", "OUTS"):
                total[f"P_{key}"] = total.get(f"P_{key}", 0) + stats[key]
    for total in owners.values():
        total["AVG"] = total["H"] / total["AB"] if total["AB"] else 0
        innings = total["P_OUTS"] / 3
        total["ERA"] = total["P_ER"] * 9 / innings if innings else 0
        total["WHIP"] = (total["P_H"] + total["P_BB"]) / innings if innings else 0
        total["IP"] = f'{total["P_OUTS"] // 3}.{total["P_OUTS"] % 3}'
    return owners


def roto_standings(totals: dict[str, dict]) -> list[dict]:
    n = len(totals)
    points = {owner: {} for owner in totals}
    for category, lower_is_better in ROTO_5X5:
        rate_category = category in {"ERA", "WHIP"}

        def ranking_key(owner: str):
            value = totals[owner][category]
            if rate_category:
                # Zero innings is unqualified and always ranks behind an owner
                # who has recorded at least one out, including a true 0.00 ERA.
                return (totals[owner].get("P_OUTS", 0) == 0, value)
            return -value if not lower_is_better else value

        ordered = sorted(totals, key=ranking_key)
        index = 0
        while index < n:
            end = index + 1
            value = totals[ordered[index]][category]
            tie_key = (totals[ordered[index]].get("P_OUTS", 0) == 0, value) if rate_category else value
            while end < n:
                next_value = totals[ordered[end]][category]
                next_key = (totals[ordered[end]].get("P_OUTS", 0) == 0, next_value) if rate_category else next_value
                if next_key != tie_key:
                    break
                end += 1
            awarded = sum(n - position for position in range(index, end)) / (end - index)
            for owner in ordered[index:end]:
                points[owner][category] = awarded
            index = end
    rows = []
    for owner in totals:
        score = sum(points[owner].values())
        rows.append({"owner": owner, "total_score": score, "category_points": points[owner], "stats": totals[owner]})
    rows.sort(key=lambda row: (-row["total_score"], row["owner"]))
    for place, row in enumerate(rows, 1):
        row["place"] = place
    return rows
