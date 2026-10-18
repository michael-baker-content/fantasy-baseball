from datetime import datetime
import pytest
from scripts.schedule_gate import decision


@pytest.mark.parametrize("hour,minute,allowed,audit", [
    (4,14,False,False), (12,59,False,False), (13,5,True,True),
    (13,35,False,False), (15,35,False,False), (23,30,False,False),
    (23,31,False,False),
])
@pytest.mark.parametrize("event,external_schedule", [
    ("schedule", False), ("workflow_dispatch", True),
])
def test_scheduled_window(hour, minute, allowed, audit, event, external_schedule):
    assert decision(datetime(2026,9,30,hour,minute), event, external_schedule,
                    {"games": {}}) == (allowed,audit)


def test_manual_request_can_run_outside_window():
    assert decision(datetime(2026,9,30,4,14), "workflow_dispatch") == (True, True)


@pytest.mark.parametrize("day,hour,minute,allowed,audit", [
    (18,16,0,False,False), (18,16,15,True,False),
    (18,16,29,True,False), (18,19,0,True,False),
    (18,19,15,False,False), (18,19,30,True,False),
    (19,19,0,False,False), (19,19,15,True,False),
    (19,22,0,True,False), (19,22,15,False,False),
    (19,22,30,True,False), (19,23,30,True,False),
    (19,23,31,False,False), (23,19,0,True,False),
    (23,22,0,True,False), (23,22,15,False,False),
    (21,13,0,True,True), (21,13,14,True,True),
    (21,13,15,False,False), (21,19,0,False,False),
])
def test_game_calendar(day, hour, minute, allowed, audit):
    assert decision(datetime(2026,10,day,hour,minute), "workflow_dispatch", True) == (allowed,audit)


def test_multiple_games_and_manual_override():
    schedule = {"games": {"2026-10-21": ["14:00", "17:00"]}}
    assert decision(datetime(2026,10,21,20,15), "schedule", schedule=schedule) == (True,False)
    assert decision(datetime(2026,10,21,20,15), "workflow_dispatch",
                    schedule={"games": {}}) == (True,True)
