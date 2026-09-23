"""Refresh all published site statistics with one local command."""

import argparse
from datetime import date, timedelta
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def refresh_site(through: date) -> None:
    outputs = [ROOT / "docs/data/league.json", ROOT / "docs/data/player-stats.json", ROOT / "docs/data/sheet-players.json"]
    previous = {path: path.read_bytes() if path.exists() else None for path in outputs}
    export_args = ["--season", str(through.year), "--through", through.isoformat(),
                   "--format", "csv", "--site"]
    steps = [
        ("Sheet selections", ["publish_sheet.py"]),
        ("Standings and owner pages", ["refresh.py", "--through", through.isoformat()]),
        ("Year-to-date Player Stats", ["export_mlb_ytd.py", *export_args]),
        ("Last 30 Days Player Stats", ["export_mlb_ytd.py", *export_args, "--last-30-days"]),
    ]
    try:
        for label, arguments in steps:
            print(f"\nUpdating {label} through {through}...", flush=True)
            subprocess.run([sys.executable, str(ROOT / arguments[0]), *arguments[1:]],
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
    args = parser.parse_args()
    through = args.through or (date.today() if args.today else date.today() - timedelta(days=1))
    if through > date.today():
        parser.error("--through cannot be in the future")
    try:
        refresh_site(through)
    except (subprocess.CalledProcessError, OSError, KeyboardInterrupt) as error:
        print(f"\nUpdate failed; do not publish. {error}", file=sys.stderr)
        return 1
    print("\nAll site statistics updated. Preview, then commit and push when ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
