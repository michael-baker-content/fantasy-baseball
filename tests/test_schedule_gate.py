from datetime import datetime
import pytest
from scripts.schedule_gate import decision


@pytest.mark.parametrize("hour,minute,allowed,audit", [
    (4,14,False,False), (12,59,False,False), (13,5,True,True),
    (13,35,True,False), (15,35,True,False), (23,30,True,False),
    (23,31,False,False),
])
def test_scheduled_window(hour, minute, allowed, audit):
    assert decision(datetime(2026,9,30,hour,minute), "schedule") == (allowed,audit)


def test_manual_request_can_run_outside_window():
    assert decision(datetime(2026,9,30,4,14), "workflow_dispatch") == (True, True)
