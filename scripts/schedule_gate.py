"""Record workflow timing and gate scheduled work by actual Pacific time."""
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def decision(local, event):
    minutes = local.hour * 60 + local.minute
    allowed = event == "workflow_dispatch" or 13 * 60 <= minutes <= 23 * 60 + 30
    audit = event == "workflow_dispatch" or (local.hour == 13 and local.minute < 35)
    return allowed, audit


def main():
    utc = datetime.now(timezone.utc)
    local = utc.astimezone(ZoneInfo("America/Los_Angeles"))
    event = os.environ.get("EVENT_NAME", "schedule")
    allowed, audit = decision(local, event)
    lines = ["## Schedule check", f"- Trigger: {event}",
             f"- UTC cron: `{os.environ.get('SCHEDULE', '')}`",
             f"- Actual start (UTC): {utc.isoformat()}",
             f"- Actual start (Pacific): {local.isoformat()}",
             f"- Decision: {'Run statistics check' if allowed else 'Skip: outside 1:00–11:30 p.m. Pacific'}",
             f"- Correction audit: {'Yes' if audit else 'No'}"]
    print("\n".join(lines))
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
        handle.write(f"allowed={str(allowed).lower()}\naudit={str(audit).lower()}\n")


if __name__ == "__main__":
    main()
