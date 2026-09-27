import pytest
import json

from mlb.client import MlbStatsClient
from scripts.check_game import game_report, inclusion_status, postseason_report


def test_inclusion_does_not_infer_from_dates_or_game_counts():
    assert inclusion_status({"included_game_ids": [123]}, 123) == "Included"
    assert inclusion_status({"included_game_ids": []}, 123) == "Not included"
    assert inclusion_status({"through_date": "2026-10-31", "games_counted": 50}, 123).startswith("Unknown")
    assert inclusion_status(None, 123).startswith("Unavailable")


def test_postseason_snapshots_are_checked_independently(tmp_path):
    data = tmp_path / "docs/data"
    data.mkdir(parents=True)
    (data / "league.json").write_text(json.dumps({"included_game_ids": [123]}))
    (data / "player-stats.json").write_text(json.dumps({"ranges": [
        {"id": "ytd", "included_game_ids": [123]},
        {"id": "postseason", "included_game_ids": []},
    ]}))
    report = "\n".join(postseason_report(123, tmp_path))
    assert "Standings / owner pages: Included" in report
    assert "Postseason Player Stats: Not included" in report


@pytest.mark.parametrize("state,complete,ready", [
    ("Final", True, True), ("Final", False, False),
    ("Live", True, False), ("Preview", False, False),
])
def test_readiness_requires_final_status_and_both_boxscores(state, complete, ready):
    team = {"players": {"ID1": {"stats": {"batting": {"atBats": 4}, "pitching": {"inningsPitched": "9.0"}}}}}
    feed = {"gameData": {"status": {"abstractGameState": state}},
            "liveData": {"boxscore": {"teams": {"away": team, "home": team if complete else {}}}}}
    report = "\n".join(game_report(feed))
    assert ("Final game with box scores available" in report) == ready
    assert "later scoring corrections" in report


def test_live_check_does_not_use_or_create_cache(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    client = MlbStatsClient(cache)
    calls = []
    def get(path, params=None):
        calls.append(path)
        return {"gameData": {"status": {"abstractGameState": "Live"}}}
    monkeypatch.setattr(client, "_get", get)
    assert client.live_game_feed(123)["gameData"]["status"]["abstractGameState"] == "Live"
    assert not cache.exists()
    cache.mkdir()
    saved = cache / "123.json"
    saved.write_text("old cached feed")
    client.live_game_feed(123)
    assert saved.read_text() == "old cached feed"
    assert calls == ["/v1.1/game/123/feed/live"] * 2
