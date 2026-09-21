import json
from pathlib import Path

from refresh import build_roster_rows, completed_games, load_config, public_payload, recalculate_payload


ROOT = Path(__file__).resolve().parents[1]


def test_config_has_seven_complete_owners_and_119_players():
    league, roster = load_config()
    assert league["start_date"] == "2026-09-01"
    assert league["end_date"] == "2026-09-27"
    assert len(league["owners"]) == 7
    assert len(roster) == 119
    assert {row["owner"] for row in roster} == set(league["owners"])
    assert league["categories"] == {
        "hitting": ["R", "HR", "RBI", "SB", "BB", "AVG"],
        "pitching": ["W", "L", "SV", "K", "ERA", "WHIP"],
    }


def test_empty_opening_snapshot_still_has_every_roster_entry():
    league, roster = load_config()
    rows = build_roster_rows(roster, {})
    payload = public_payload(league, [], rows)
    assert len(payload["standings"]) == 7
    assert sum(len(owner["players"]) for owner in payload["owners"]) == 119
    assert payload["games_counted"] == 0
    assert all(len(row["category_points"]) == 12 for row in payload["standings"])
    assert all(row["total_score"] == 48 for row in payload["standings"])


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
    assert len(payload["standings"]) == 7
    assert len(payload["owners"]) == 7


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
    assert sum(row["total_score"] for row in recalculated["standings"]) == 12 * sum(range(1, 8))
