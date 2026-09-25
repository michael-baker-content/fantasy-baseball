import pytest

from scripts.seed_sheet import draft_score, select_players


def test_innings_are_baseball_outs_and_saves_boost_relief_pitchers():
    assert draft_score({"stats": {"IP": "10.2"}}, "pitchers") == pytest.approx(10 + 2 / 3)
    assert draft_score({"stats": {"IP": "50.0", "SV": 30}}, "pitchers") > draft_score({"stats": {"IP": "150.0", "K": 150}}, "pitchers")


def test_per_team_quotas_deduplication_and_incidental_pitching():
    batters = [{"id": i, "name": f"B{i}", "team": "Club", "position": "OF", "stats": {"AB": i}} for i in range(1, 14)]
    pitchers = [{"id": i, "name": f"P{i}", "team": "Club", "position": "P", "stats": {"IP": str(i)}} for i in range(20, 30)]
    pitchers.append({**batters[0], "stats": {"IP": "999"}})
    payload = {"ranges": [{"id": "ytd", "teams": ["Club", "Empty"], "batters": batters + [batters[-1]], "pitchers": pitchers}]}
    selected, counts = select_players(payload)
    assert selected == {str(i) for i in [*range(3, 14), *range(22, 30)]}
    assert counts["Club", "batters"] == 11
    assert counts["Club", "pitchers"] == 8
    assert counts["Empty", "batters"] == 0
