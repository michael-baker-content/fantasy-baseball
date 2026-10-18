"""Record workflow timing and gate scheduled work by actual Pacific time."""
import os
import json
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


SCHEDULE_PATH = Path(__file__).resolve().parents[1] / "config" / "update_schedule.json"


def decision(local, event, external_schedule=False, schedule=None):
    minutes = local.hour * 60 + local.minute
    manual = event == "workflow_dispatch" and not external_schedule
    if manual:
        return True, True
    if not 13 * 60 <= minutes <= 23 * 60 + 30:
        return False, False
    # Treat a slightly delayed run as belonging to its quarter-hour slot.
    slot = minutes // 15 * 15
    if slot == 13 * 60:
        return True, True
    if schedule is None:
        schedule = json.loads(SCHEDULE_PATH.read_text(encoding="utf-8"))
    starts = schedule["games"].get(local.date().isoformat(), [])
    for start in starts:
        hour, minute = map(int, start.split(":"))
        first_pitch = hour * 60 + minute
        if first_pitch + 120 <= slot <= first_pitch + 300:
            return True, False
        if slot > first_pitch + 300 and slot % 30 == 0:
            return True, False
    return False, False


def main():
    utc = datetime.now(timezone.utc)
    local = utc.astimezone(ZoneInfo("America/Los_Angeles"))
    event = os.environ.get("EVENT_NAME", "schedule")
    external_schedule = os.environ.get("EXTERNAL_SCHEDULE", "").lower() == "true"
    allowed, audit = decision(local, event, external_schedule)
    lines = ["## Schedule check", f"- Trigger: {event}",
             f"- External scheduled request: {'Yes' if external_schedule else 'No'}",
             f"- UTC cron: `{os.environ.get('SCHEDULE', '')}`",
             f"- Actual start (UTC): {utc.isoformat()}",
             f"- Actual start (Pacific): {local.isoformat()}",
             f"- Decision: {'Run statistics check' if allowed else 'Skip: no check due in this Pacific time slot'}",
             f"- Correction audit: {'Yes' if audit else 'No'}"]
    print("\n".join(lines))
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
        handle.write(f"allowed={str(allowed).lower()}\naudit={str(audit).lower()}\n")


if __name__ == "__main__":
    main()
