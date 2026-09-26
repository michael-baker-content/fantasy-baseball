from scripts.refresh import build_roster_rows, public_payload
from scripts.publish_postseason import postseason_range
from mlb.live_scoring import appearance_stats
from mlb.postseason import aggregate_feeds
import json
from scripts import refresh, publish_postseason


def test_no_appearances_are_null_and_tied_at_bottom():
    league = {"owners": ["A", "B"], "game_types": "F,D,L,W", "categories": {"hitting": ["R", "AVG"], "pitching": ["W", "ERA"]}}
    rows = build_roster_rows([{"owner": "A", "section": "hitting", "player_id": 1, "player_name": "A"}], {})
    payload = public_payload(league, [], rows)
    assert [row["place"] for row in payload["standings"]] == [1, 1]
    assert all(row["total_score"] is None for row in payload["standings"])
    assert payload["owners"][0]["players"][0]["stats"]["R"] is None
    rows[0]["stats"].update(G=1, AB=1)
    payload = public_payload(league, [], rows)
    assert payload["standings"][0]["owner"] == "A"
    assert payload["standings"][0]["stats"]["R"] == 0
    assert payload["standings"][0]["stats"]["W"] is None
    assert payload["standings"][1]["total_score"] is None


def test_postseason_preserves_pool_and_regular_range():
    player = {"id": 1, "name": "Player", "team": "Club", "stats": {"HR": 30}}
    source = {"id": "ytd", "season": 2026, "teams": ["Club"], "roster_date": "2026-09-27", "batters": [player], "pitchers": []}
    result = postseason_range({"ranges": [source]}, {"season": 2026, "start_date": "2026-09-29"}, {}, "2026-09-26")
    assert result["batters"][0]["stats"]["HR"] is None
    assert source["batters"][0]["stats"]["HR"] == 30


def test_zero_out_appearance_has_zero_counts_but_no_rates():
    stats = {"G": 1, "OUTS": 0, "W": 0, "ERA": 0, "WHIP": 0}
    result = appearance_stats(stats, "pitching")
    assert result["W"] == 0
    assert result["ERA"] is None
    assert result["WHIP"] is None


def test_preseason_publishers_do_not_fetch_mlb_data(tmp_path, monkeypatch):
    league = {"owners": ["A", "B", "C"], "season": 2026,
              "start_date": "2026-09-29", "end_date": "2026-10-31",
              "game_types": "F,D,L,W", "categories": {"hitting": ["R"], "pitching": ["W"]}}
    data = tmp_path / "docs/data"
    data.mkdir(parents=True)
    regular = {"id": "ytd", "season": 2026, "teams": [], "roster_date": "2026-09-26",
               "batters": [], "pitchers": []}
    (data / "player-stats.json").write_text(json.dumps({"ranges": [regular]}))

    class OfflineClient:
        def __init__(self, *args):
            pass

        def schedule(self, *args):
            raise AssertionError("Before opening day no MLB request is needed")

    for module in (refresh, publish_postseason):
        monkeypatch.setattr(module, "ROOT", tmp_path)
        monkeypatch.setattr(module, "load_config", lambda: (league, []))
        monkeypatch.setattr(module, "MlbStatsClient", OfflineClient)
        monkeypatch.setattr("sys.argv", ["publish", "--through", "2026-09-26"])
        module.main()
    result = json.loads((data / "league.json").read_text())
    assert result["games_counted"] == 0
    assert all(row["total_score"] is None for row in result["standings"])
    ranges = json.loads((data / "player-stats.json").read_text())["ranges"]
    assert ranges[0]["id"] == "postseason"
    assert ranges[1]["batters"] == regular["batters"]


def test_boxscore_appearance_without_games_played_and_unused_bench():
    feed = {"liveData": {"boxscore": {"teams": {"home": {"players": {
        "ID1": {"person": {"id": 1}, "stats": {"batting": {"atBats": 1, "hits": 0}}},
        "ID2": {"person": {"id": 2}, "stats": {"batting": {}, "pitching": {}}},
        "ID3": {"person": {"id": 3}, "stats": {"pitching": {"inningsPitched": "0.0", "baseOnBalls": 1}}},
    }}}}}}
    pool = aggregate_feeds([feed])
    assert pool[1]["hitting"]["gamesPlayed"] == 1
    assert pool[2]["hitting"]["gamesPlayed"] == 0
    assert pool[3]["pitching"]["gamesPlayed"] == 1
