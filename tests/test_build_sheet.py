import json

import pytest

from scripts.build_sheet import build_rows, parse_positions


def test_positions_default_to_primary_and_preserve_manual_arrays():
    player = {"id": 1, "name": "Test Player", "team": "Boston Red Sox", "position": "CF"}
    payload = {"ranges": [{"id": "ytd", "batters": [player], "pitchers": [player]}]}
    rows = build_rows(payload, {"1": "Yes"})
    assert len(rows) == 1
    assert rows[0]["Sheet"] == "Yes"
    assert json.loads(rows[0]["Positions"]) == ["CF"]
    assert json.loads(build_rows(payload, {}, {"1": ["1B", "OF"]})[0]["Positions"]) == ["1B", "OF"]
    assert json.loads(build_rows(payload, {}, {"1": []})[0]["Positions"]) == []


@pytest.mark.parametrize("value", ['"CF"', 'null', '{}', '[1]', '[""]', 'CF,OF'])
def test_positions_require_json_array_of_nonempty_strings(value):
    with pytest.raises(ValueError):
        parse_positions(value)


def test_refreshed_pool_removes_departed_players_and_preserves_manual_edits():
    payload = {"ranges": [{"id": "ytd", "batters": [
        {"id": 1, "name": "Retained Player", "team": "Boston Red Sox", "position": "CF"},
        {"id": 3, "name": "New Player", "team": "Boston Red Sox", "position": "SS"},
    ], "pitchers": []}]}
    rows = build_rows(payload, {"1": "Yes", "2": "Yes"}, {"1": ["LF", "RF"], "2": ["RP"]})
    by_id = {row["MLB ID"]: row for row in rows}
    assert set(by_id) == {"1", "3"}
    assert by_id["1"]["Sheet"] == "Yes"
    assert json.loads(by_id["1"]["Positions"]) == ["LF", "RF"]
    assert by_id["3"]["Sheet"] == "No"
    assert json.loads(by_id["3"]["Positions"]) == ["SS"]
