import json
from pathlib import Path

import pytest

from scripts.refresh import build_roster_rows, completed_games, load_config, public_payload, recalculate_payload
from mlb.scoring import scoring_categories


ROOT = Path(__file__).resolve().parents[1]


def test_config_has_complete_owners_and_rosters():
    league, roster = load_config()
    assert league["start_date"] == "2026-09-01"
    assert league["end_date"] == "2026-09-27"
    assert len(league["owners"]) == len(set(league["owners"]))
    assert len(roster) == 17 * len(league["owners"])
    assert {row["owner"] for row in roster} == set(league["owners"])
    assert league["categories"] == {
        "hitting": ["R", "HR", "RBI", "SB", "BB", "AVG"],
        "pitching": ["W", "L", "SV", "K", "ERA", "WHIP"],
    }


def test_empty_opening_snapshot_still_has_every_roster_entry():
    league, roster = load_config()
    rows = build_roster_rows(roster, {})
    payload = public_payload(league, [], rows)
    assert len(payload["standings"]) == len(league["owners"])
    assert sum(len(owner["players"]) for owner in payload["owners"]) == len(roster)
    assert payload["games_counted"] == 0
    assert all(len(row["category_points"]) == 12 for row in payload["standings"])
    assert all(row["total_score"] == 12 * (len(league["owners"]) + 1) / 2 for row in payload["standings"])


def test_only_completed_games_are_counted():
    schedule = {"dates": [{"games": [
        {"gamePk": 1, "status": {"abstractGameState": "Final"}},
        {"gamePk": 2, "status": {"abstractGameState": "Live"}},
        {"gamePk": 3, "status": {"abstractGameState": "Preview"}},
    ]}]}
    assert [game["gamePk"] for game in completed_games(schedule)] == [1]


def test_generated_site_payload_is_valid():
    payload = json.loads((ROOT / "docs/data/league.json").read_text(encoding="utf-8"))
    assert payload["league"]["name"] == "BABBD Roto"
    expected = set(payload["league"]["owners"])
    assert {row["owner"] for row in payload["standings"]} == expected
    assert {row["name"] for row in payload["owners"]} == expected
    assert len(payload["standings"]) == len(payload["owners"]) == len(expected)


def test_offline_recalculation_preserves_snapshot_and_adds_categories():
    league, _ = load_config()
    original = json.loads((ROOT / "docs/data/league.json").read_text(encoding="utf-8"))
    recalculated = recalculate_payload(original, league["categories"])
    assert recalculated["league"]["categories"] == league["categories"]
    for field in ("updated_at", "through_date", "games_counted"):
        assert recalculated[field] == original[field]
    for before, after in zip(original["owners"], recalculated["owners"]):
        assert before["players"] == after["players"]
    for standing in recalculated["standings"]:
        assert len(standing["category_points"]) == 12
        assert standing["total_score"] == sum(standing["category_points"].values())
    owner_count = len(original["league"]["owners"])
    assert sum(row["total_score"] for row in recalculated["standings"]) == 12 * sum(range(1, owner_count + 1))


def test_refresh_and_recalculation_use_configured_categories():
    league, roster = load_config()
    categories = {"hitting": ["BB"], "pitching": ["L"]}
    rows = build_roster_rows(roster, {})
    refreshed = public_payload(league | {"categories": categories}, [], rows)
    original = public_payload(league, [], rows)
    recalculated = recalculate_payload(original, categories)
    for payload in (refreshed, recalculated):
        assert payload["league"]["categories"] == categories
        assert all(list(row["category_points"]) == ["BB", "L"] for row in payload["standings"])
        # Two tied categories each award the mean of points 1 through N.
        expected_tied_score = len(league["owners"]) + 1
        assert all(row["total_score"] == expected_tied_score for row in payload["standings"])
    assert original["league"]["categories"] == league["categories"]
    assert scoring_categories(categories) == (("BB", False), ("L", True))


@pytest.mark.parametrize("categories", [
    {"hitting": ["BB", "BB"], "pitching": []},
    {"hitting": ["L"], "pitching": []},
    {"hitting": [], "pitching": ["NOT_A_STAT"]},
    {"hitting": [], "pitching": []},
])
def test_invalid_scoring_configuration_is_rejected(categories):
    with pytest.raises(ValueError):
        scoring_categories(categories)
