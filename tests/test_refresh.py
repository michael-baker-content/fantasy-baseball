import json
from pathlib import Path

from refresh import build_roster_rows, load_config, public_payload


ROOT = Path(__file__).resolve().parents[1]


def test_config_has_seven_complete_owners_and_119_players():
    league, roster = load_config()
    assert league["start_date"] == "2026-08-24"
    assert league["end_date"] == "2026-09-20"
    assert len(league["owners"]) == 7
    assert len(roster) == 119
    assert {row["owner"] for row in roster} == set(league["owners"])


def test_empty_opening_snapshot_still_has_every_roster_entry():
    league, roster = load_config()
    rows = build_roster_rows(roster, {})
    payload = public_payload(league, [], rows)
    assert len(payload["standings"]) == 7
    assert sum(len(owner["players"]) for owner in payload["owners"]) == 119
    assert payload["games_counted"] == 0


def test_generated_site_payload_is_valid():
    payload = json.loads((ROOT / "docs/data/league.json").read_text(encoding="utf-8"))
    assert payload["league"]["name"] == "BABBD Roto"
    assert len(payload["standings"]) == 7
    assert len(payload["owners"]) == 7
