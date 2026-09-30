import json
from datetime import date

import pytest
from scripts import auto_update as module


def setup(tmp_path):
    league = {"phase": "postseason", "game_types": "F,D,L,W", "season": 2026,
              "start_date": "2026-09-29", "end_date": "2026-10-31", "owners": ["Owner"],
              "categories": {"hitting": ["R"], "pitching": ["W"]}}
    roster = [{"owner": "Owner", "player_id": 1, "player_name": "Test Player", "section": "hitting"}]
    data = tmp_path / "docs/data"
    data.mkdir(parents=True)
    saved = module.public_payload(league, [], module.build_roster_rows(roster, {}))
    (data / "league.json").write_text(json.dumps(saved))
    ytd = {"id": "ytd", "season": 2026, "teams": ["Club"], "roster_date": "2026-09-27",
           "batters": [{"id": 1, "name": "Test Player", "stats": {"R": 100}}], "pitchers": []}
    (data / "player-stats.json").write_text(json.dumps({"ranges": [ytd]}))
    (data / "sheet-players.json").write_text('{"untouched":true}')
    return league, roster, data, ytd


class Client:
    def __init__(self):
        self.calls = []
        self.runs = 1
        self.broken = False

    def schedule(self, *args):
        self.calls.append("schedule")
        return {"dates": [{"games": [{"gamePk": 123, "officialDate": "2026-09-29",
                                     "status": {"abstractGameState": "Final"}}]}]}

    def live_game_feed(self, pk):
        self.calls.append(pk)
        team = {"players": {"ID1": {"person": {"id": 1}, "stats": {
            "batting": {"runs": self.runs, "atBats": 4}, "pitching": {"inningsPitched": "9.0"}}}}}
        return {"gameData": {"status": {"abstractGameState": "Final"}},
                "liveData": {"boxscore": {"teams": {} if self.broken else {"away": team, "home": team}}}}


def test_new_game_then_noop_and_correction(tmp_path):
    league, roster, data, ytd = setup(tmp_path)
    client = Client()
    today = date(2026, 9, 29)
    assert module.refresh_if_needed(league, roster, client, today, root=tmp_path)
    before = {path: path.read_bytes() for path in data.iterdir()}
    assert json.loads((data / "player-stats.json").read_text())["ranges"][1] == ytd
    client.calls.clear()
    assert not module.refresh_if_needed(league, roster, client, today, root=tmp_path)
    assert client.calls == ["schedule"]
    assert not module.refresh_if_needed(league, roster, client, date(2026, 9, 30), audit=True, root=tmp_path)
    assert all(path.read_bytes() == content for path, content in before.items())
    client.runs = 2
    assert module.refresh_if_needed(league, roster, client, today, audit=True, root=tmp_path)
    assert json.loads((data / "league.json").read_text())["included_game_ids"] == [123]
    assert (data / "sheet-players.json").read_text() == '{"untouched":true}'


@pytest.mark.parametrize("phase,today", [("regular", date(2026, 9, 29)),
                                         ("postseason", date(2026, 9, 28)),
                                         ("postseason", date(2026, 11, 2))])
def test_disabled_or_outside_window_makes_no_requests(tmp_path, phase, today):
    league, roster, _, _ = setup(tmp_path)
    client = Client()
    assert not module.refresh_if_needed(league | {"phase": phase}, roster, client, today, root=tmp_path)
    assert client.calls == []


def test_bad_feed_leaves_snapshots_unchanged(tmp_path):
    league, roster, data, _ = setup(tmp_path)
    before = {path: path.read_bytes() for path in data.iterdir()}
    client = Client()
    client.broken = True
    with pytest.raises(ValueError, match="retaining saved data"):
        module.refresh_if_needed(league, roster, client, date(2026, 9, 29), root=tmp_path)
    assert all(path.read_bytes() == content for path, content in before.items())
