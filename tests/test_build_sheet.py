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
