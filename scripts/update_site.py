"""Refresh all published site statistics with one local command."""

import argparse
from datetime import date, timedelta
from pathlib import Path
import subprocess
import sys
import json

ROOT = Path(__file__).resolve().parents[1]


def refresh_site(through: date, league=None, prepare=False) -> None:
    league = league or {"phase": "regular", "season": through.year, "regular_season_end": f"{through.year}-09-27"}
    regular_through = min(through.isoformat(), league["regular_season_end"])
    outputs = [ROOT / "docs/data/league.json", ROOT / "docs/data/player-stats.json", ROOT / "docs/data/sheet-players.json"]
    previous = {path: path.read_bytes() if path.exists() else None for path in outputs}
    export_args = ["--season", str(league["season"]), "--through", regular_through,
                   "--format", "csv", "--site"]
    steps = [
        ("Sheet selections", ["publish_sheet.py"]),
        ("Standings and owner pages", ["refresh.py", "--through", through.isoformat()]),
        ("Year-to-date Player Stats", ["export_mlb_ytd.py", *export_args]),
        ("Last 30 Days Player Stats", ["export_mlb_ytd.py", *export_args, "--last-30-days"]),
    ]
    if league.get("phase") == "postseason" or prepare:
        steps = steps[:2]
    if league.get("game_types") == "F,D,L,W":
        steps.append(("Postseason Player Stats", ["publish_postseason.py", "--through", through.isoformat()]))
    try:
        for label, arguments in steps:
            print(f"\nUpdating {label} through {through}...", flush=True)
            subprocess.run([sys.executable, "-m", f"scripts.{Path(arguments[0]).stem}", *arguments[1:]],
                           cwd=ROOT, check=True)
    except (subprocess.CalledProcessError, OSError, KeyboardInterrupt):
        for path, content in previous.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(content)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    period = parser.add_mutually_exclusive_group()
    period.add_argument("--today", action="store_true", help="include today's available statistics")
    period.add_argument("--through", type=date.fromisoformat, metavar="YYYY-MM-DD",
                        help="use a specific cutoff instead of yesterday")
    period.add_argument("--prepare", action="store_true", help="initialize postseason dashes before opening day without MLB downloads")
    args = parser.parse_args()
    league = json.loads((ROOT / "config/league.json").read_text(encoding="utf-8"))
    if args.prepare and (date.today().isoformat() >= league["start_date"] or league.get("game_types") != "F,D,L,W"):
        parser.error("--prepare is only available before the configured postseason start")
    through = args.through or (date.today() if args.today or league.get("phase") == "postseason" else date.today() - timedelta(days=1))
    if through > date.today():
        parser.error("--through cannot be in the future")
    try:
        refresh_site(through, league, prepare=args.prepare)
    except (subprocess.CalledProcessError, OSError, KeyboardInterrupt) as error:
        print(f"\nUpdate failed; do not publish. {error}", file=sys.stderr)
        return 1
    print("\nAll site statistics updated. Preview, then commit and push when ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
