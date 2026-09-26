import json
from pathlib import Path

import pytest
from scripts import refresh

from scripts.refresh import build_roster_rows, completed_games, load_config, public_payload, recalculate_payload, validate_config
from mlb.scoring import scoring_categories


ROOT = Path(__file__).resolve().parents[1]


def test_check_config_is_offline(monkeypatch, capsys):
    league = {"owners": ["A"], "categories": {"hitting": ["R"], "pitching": ["W"]}}
    monkeypatch.setattr(refresh, "load_config", lambda: (league, []))
    monkeypatch.setattr("sys.argv", ["refresh", "--check-config"])
    def no_network(*args, **kwargs):
        raise AssertionError("Configuration checks must not construct an API client")
    monkeypatch.setattr(refresh, "MlbStatsClient", no_network)
    assert refresh.main() == 0
    assert "1 owners, 0 roster entries" in capsys.readouterr().out


def test_recalculate_rejects_changed_owner_pool(tmp_path, monkeypatch):
    data_path = tmp_path / "docs/data/league.json"
    data_path.parent.mkdir(parents=True)
    saved = {"league": {"owners": ["A"]}, "owners": [{"name": "A", "players": []}]}
    data_path.write_text(json.dumps(saved), encoding="utf-8")
    monkeypatch.setattr(refresh, "ROOT", tmp_path)
    monkeypatch.setattr(refresh, "load_config", lambda: ({"owners": ["A", "B"]}, []))
    monkeypatch.setattr("sys.argv", ["refresh", "--recalculate"])
    with pytest.raises(SystemExit) as error:
        refresh.main()
    assert error.value.code == 2
    assert json.loads(data_path.read_text()) == saved


def test_config_has_complete_owners_and_rosters():
    league, roster = load_config()
    assert len(league["owners"]) == len(set(league["owners"]))
    assert {row["owner"] for row in roster} <= set(league["owners"])
    validate_config(league, roster)


def test_empty_opening_snapshot_still_has_every_roster_entry():
    league, roster = load_config()
    rows = build_roster_rows(roster, {})
    payload = public_payload(league, [], rows)
    assert len(payload["standings"]) == len(league["owners"])
    assert sum(len(owner["players"]) for owner in payload["owners"]) == len(roster)
    assert payload["games_counted"] == 0
    count = len(scoring_categories(league["categories"]))
    assert all(len(row["category_points"]) == count for row in payload["standings"])
    assert all(row["total_score"] == count * (len(league["owners"]) + 1) / 2 for row in payload["standings"])


def test_only_completed_games_are_counted():
    schedule = {"dates": [{"games": [
        {"gamePk": 1, "status": {"abstractGameState": "Final"}},
        {"gamePk": 2, "status": {"abstractGameState": "Live"}},
        {"gamePk": 3, "status": {"abstractGameState": "Preview"}},
    ]}]}
    assert [game["gamePk"] for game in completed_games(schedule)] == [1]


def test_generated_site_payload_is_valid():
    payload = json.loads((ROOT / "docs/data/league.json").read_text(encoding="utf-8"))
    assert payload["league"]["name"]
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
        assert len(standing["category_points"]) == len(scoring_categories(league["categories"]))
        assert standing["total_score"] == sum(standing["category_points"].values())
    owner_count = len(original["league"]["owners"])
    count = len(scoring_categories(league["categories"]))
    assert sum(row["total_score"] for row in recalculated["standings"]) == count * sum(range(1, owner_count + 1))


@pytest.mark.parametrize("size", [1, 2, 7, 8, 12])
def test_owner_pool_sizes_include_empty_and_one_sided_rosters(size):
    owners = [f"Owner {index}" for index in range(size)]
    league = {"owners": owners, "categories": {"hitting": ["R", "AVG"], "pitching": ["W", "ERA", "WHIP"]}}
    roster = [{"owner": owners[0], "section": "hitting", "slot": "C", "player_id": 1, "player_name": "Hitter"}]
    if size > 1:
        roster.append({"owner": owners[1], "section": "pitching", "slot": "P", "player_id": 2, "player_name": "Pitcher"})
    validate_config(league, roster)
    payload = public_payload(league, [], build_roster_rows(roster, {}))
    recalculated = recalculate_payload(payload, league["categories"])
    for result in (payload, recalculated):
        assert [owner["name"] for owner in result["owners"]] == owners
        assert len(result["standings"]) == size
        assert all(row["total_score"] == 5 * (size + 1) / 2 for row in result["standings"])
        assert sum(row["total_score"] for row in result["standings"]) == 5 * size * (size + 1) / 2


@pytest.mark.parametrize("owners,roster", [
    ([], []), (["A", "a"], []), ([" A"], []),
    (["A"], [{"owner": "Other"}]),
    (["A"], [{"owner": "A", "section": "unknown"}]),
    (["A"], [{"owner": "A", "section": "hitting", "player_id": "bad"}]),
])
def test_invalid_owner_configuration_has_actionable_error(owners, roster):
    with pytest.raises(ValueError, match="config/"):
        validate_config({"owners": owners, "categories": {"hitting": ["R"], "pitching": ["W"]}}, roster)


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
