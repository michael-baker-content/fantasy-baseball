import json

import pytest

from scripts.refresh import validate_config
from scripts.roster_status import apply_eliminations


def test_elimination_uses_postseason_pool_and_preserves_statistics(tmp_path):
    folder = tmp_path / "docs/data"
    folder.mkdir(parents=True)
    pool = {"ranges": [
        {"id": "ytd", "batters": [{"id": 1, "team": "Houston Astros"}]},
        {"id": "postseason", "batters": [{"id": 1, "team": "Boston Red Sox"}],
         "pitchers": [{"id": 2, "team_abbreviation": "BOS"}]},
    ]}
    (folder / "player-stats.json").write_text(json.dumps(pool))
    payload = {"league": {}, "standings": [{"total_score": 12}],
               "owners": [{"players": [{"player_id": i, "stats": {"R": 2}}
                                        for i in (1, 2, 3)], "totals": {"R": 6}}]}
    marked = apply_eliminations(payload, {"eliminated_teams": ["BOS"]}, tmp_path)
    assert [p["eliminated"] for p in marked["owners"][0]["players"]] == [True, True, False]
    assert marked["standings"] == payload["standings"]
    assert marked["owners"][0]["totals"] == {"R": 6}
    assert all(p["stats"] == {"R": 2} for p in marked["owners"][0]["players"])
    restored = apply_eliminations(marked, {"eliminated_teams": []}, tmp_path)
    assert not any(p["eliminated"] for p in restored["owners"][0]["players"])
    assert "eliminated" not in payload["owners"][0]["players"][0]


@pytest.mark.parametrize("value", ["BOS", ["bos"], ["BOS", "BOS"], ["XYZ"], [None]])
def test_invalid_elimination_config_rejected(value):
    league = {"owners": ["Owner"], "categories": {"hitting": ["R"], "pitching": ["W"]},
              "eliminated_teams": value}
    with pytest.raises(ValueError, match="eliminated_teams"):
        validate_config(league, [])
