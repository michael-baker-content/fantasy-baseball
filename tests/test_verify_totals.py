import copy
import pytest
from scripts import verify_totals as module


def fixture():
    boxes = {}
    for side, pid in (("away", 1), ("home", 2)):
        batting = dict.fromkeys(module.FIELDS["hitting"], 0) | {"atBats": 4, "hits": 1}
        pitching = dict.fromkeys(module.FIELDS["pitching"], 0) | {"inningsPitched": "9.0", "strikeOuts": 3}
        boxes[side] = {"players": {str(pid): {"person": {"id": pid, "fullName": f"Player {pid}"},
                                              "stats": {"batting": batting, "pitching": pitching}}}}
    feed = {"gameData": {"game": {"type": "R"}, "status": {"abstractGameState": "Final"},
                         "datetime": {"officialDate": "2026-09-27"},
                         "teams": {"away": {"id": 10}, "home": {"id": 20}}},
            "liveData": {"boxscore": {"teams": boxes}}}
    row = {"gamePk": 123, "officialDate": "2026-09-27", "status": {"abstractGameState": "Final"},
           "teams": {"away": {"team": {"id": 10}}, "home": {"team": {"id": 20}}}}
    return feed, row


@pytest.mark.parametrize("scenario", ["match", "double", "missing", "different", "incomplete", "live"])
def test_verification_outcomes(monkeypatch, scenario):
    feed, row = fixture()
    rows = [row]
    if scenario in {"double", "live"}:
        other = copy.deepcopy(row)
        other["gamePk"] = 124
        if scenario == "live":
            other["status"]["abstractGameState"] = "Live"
        rows.append(other)
    class Client:
        def schedule(self, start, through, types):
            assert start == through == "2026-09-27" and types == "R"
            return {"dates": [{"games": rows}]}
        def live_game_feed(self, pk):
            assert pk == 124
            return feed
    def splits(group, season, through, start):
        assert season == 2026 and start == through == "2026-09-27"
        result = []
        for side, pid in (("away", 1), ("home", 2)):
            stat = dict(feed["liveData"]["boxscore"]["teams"][side]["players"][str(pid)]["stats"]["batting" if group == "hitting" else "pitching"])
            if scenario == "double":
                stat = {key: "18.0" if key == "inningsPitched" else value * 2 for key, value in stat.items()}
            if scenario == "different" and group == "hitting":
                stat["hits"] = 0
            if scenario == "missing" and pid == 1:
                continue
            if scenario == "incomplete":
                stat.pop("hits")
            result.append({"player": {"id": pid}, "stat": stat})
        return result
    monkeypatch.setattr(module, "season_splits", splits)
    if scenario == "incomplete":
        with pytest.raises(ValueError, match="Missing hits"):
            module.verify_totals(Client(), 123, feed)
        return
    text = "\n".join(module.verify_totals(Client(), 123, feed))
    expected = "Unable to verify" if scenario == "live" else "Totals not yet matching" if scenario in {"missing", "different"} else "Daily totals match"
    assert expected in text


def test_nonfinal_and_postseason_do_not_query_daily_totals():
    feed, _ = fixture()
    feed["gameData"]["status"]["abstractGameState"] = "Live"
    assert "Unable to verify" in module.verify_totals(None, 123, feed)[0]
    feed["gameData"]["game"]["type"] = "W"
    assert "Not applicable" in module.verify_totals(None, 123, feed)[0]
