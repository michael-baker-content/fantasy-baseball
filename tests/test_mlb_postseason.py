from mlb.postseason import innings_to_outs
from mlb.scoring import roto_standings


def test_baseball_innings_are_converted_to_outs():
    assert innings_to_outs("6.2") == 20
    assert innings_to_outs("0.1") == 1
    assert innings_to_outs("7.0") == 21


def test_roto_ties_split_available_points():
    base = {"HR": 0, "RBI": 0, "SB": 0, "BB": 0, "AVG": 0, "W": 0, "L": 0, "SV": 0, "K": 0, "ERA": 9, "WHIP": 9, "P_OUTS": 3}
    totals = {
        "A": base | {"R": 10},
        "B": base | {"R": 10},
        "C": base | {"R": 5},
    }
    rows = {row["owner"]: row for row in roto_standings(totals)}
    assert rows["A"]["category_points"]["R"] == 2.5
    assert rows["B"]["category_points"]["R"] == 2.5
    assert rows["C"]["category_points"]["R"] == 1


def test_zero_innings_rank_last_in_rate_categories():
    base = {"R": 0, "HR": 0, "RBI": 0, "SB": 0, "BB": 0, "AVG": 0, "W": 0, "L": 0, "SV": 0, "K": 0}
    totals = {
        "Scoreless": base | {"ERA": 0, "WHIP": 0, "P_OUTS": 3},
        "No innings A": base | {"ERA": 0, "WHIP": 0, "P_OUTS": 0},
        "No innings B": base | {"ERA": 0, "WHIP": 0, "P_OUTS": 0},
    }
    rows = {row["owner"]: row for row in roto_standings(totals)}
    assert rows["Scoreless"]["category_points"]["ERA"] == 3
    assert rows["Scoreless"]["category_points"]["WHIP"] == 3
    assert rows["No innings A"]["category_points"]["ERA"] == 1.5
    assert rows["No innings B"]["category_points"]["WHIP"] == 1.5


def test_six_by_six_rewards_more_walks_and_fewer_losses():
    base = {"R": 0, "HR": 0, "RBI": 0, "SB": 0, "AVG": 0,
            "W": 0, "SV": 0, "K": 0, "ERA": 3, "WHIP": 1, "P_OUTS": 9}
    totals = {
        "A": base | {"BB": 10, "L": 0},
        "B": base | {"BB": 5, "L": 2},
        "C": base | {"BB": 5, "L": 2},
    }
    rows = {row["owner"]: row for row in roto_standings(totals)}
    assert list(rows["A"]["category_points"]) == [
        "R", "HR", "RBI", "SB", "BB", "AVG", "W", "L", "SV", "K", "ERA", "WHIP",
    ]
    assert rows["A"]["category_points"]["BB"] == 3
    assert rows["A"]["category_points"]["L"] == 3
    assert rows["B"]["category_points"]["BB"] == 1.5
    assert rows["B"]["category_points"]["L"] == 1.5
    assert rows["A"]["total_score"] == 26
    assert rows["B"]["total_score"] == rows["C"]["total_score"] == 23


def test_historical_five_by_five_remains_available():
    from mlb.scoring import ROTO_5X5
    totals = {"A": {category: 0 for category, _ in ROTO_5X5}}
    row = roto_standings(totals, categories=ROTO_5X5)[0]
    assert len(row["category_points"]) == 10
    assert row["total_score"] == 10
