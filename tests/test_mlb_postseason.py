from mlb.postseason import innings_to_outs
from mlb.scoring import roto_standings


def test_baseball_innings_are_converted_to_outs():
    assert innings_to_outs("6.2") == 20
    assert innings_to_outs("0.1") == 1
    assert innings_to_outs("7.0") == 21


def test_roto_ties_split_available_points():
    base = {"HR": 0, "RBI": 0, "SB": 0, "AVG": 0, "W": 0, "SV": 0, "K": 0, "ERA": 9, "WHIP": 9, "P_OUTS": 3}
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
    base = {"R": 0, "HR": 0, "RBI": 0, "SB": 0, "AVG": 0, "W": 0, "SV": 0, "K": 0}
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
