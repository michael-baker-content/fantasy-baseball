# BABBD Roto

A static fantasy baseball tracker for a seven-owner rotisserie league. The site
runs on GitHub Pages; a local Python command downloads completed MLB games and
regenerates the public standings data.

## League setup

- Dates: August 24 through September 20, 2026 (inclusive)
- Owners and rosters: copied from the 2025 BABBD playoff workbook
- Hitting: R, HR, RBI, SB, AVG
- Pitching: W, SV, K, ERA, WHIP
- Scoring: 7 points for first through 1 point for last; ties split points

## Refresh standings

```powershell
.venv\Scripts\python.exe refresh.py
```

Use `--through YYYY-MM-DD` to reproduce a particular day. Completed raw MLB
game feeds are cached in `data/mlb_cache`. Add `--refresh` to redownload them.

The command writes `docs/data/league.json`, which the static site reads. Preview
the `docs` folder with any local static web server, then commit and push the
updated JSON when it is ready to publish.

Preview locally from the repository root:

```powershell
.venv\Scripts\python.exe -m http.server 8000 --directory docs
```

Then open `http://localhost:8000` and press `Ctrl+C` when finished.

## League configuration

- `config/league.json`: dates, categories, name, and owners
- `config/roster.csv`: owner, section, roster slot, MLB ID, and player name

## GitHub Pages

In the repository settings, choose **Deploy from a branch**, select the default
branch, and use the `/docs` folder. No Python process or database is required on
the hosting side.

The `reference/` folder and downloaded `data/mlb_cache/` feeds are intentionally
excluded from Git. The generated public JSON in `docs/data/` is committed so
GitHub Pages can serve the latest standings.

## Historical validation

```powershell
.venv\Scripts\python.exe reproduce_2025.py
```

This rebuilds the 2025 postseason from MLB box scores. It resolves 119 drafted
entries and reconciles all 84 owner/category totals in the reference workbook.

## Export likely playoff-team player statistics

`export_mlb_ytd.py` exports combined regular-season totals for players currently
affiliated with the likely playoff teams listed in its `PLAYOFF_TEAMS` setting.
Released players and free agents are omitted; optioned and injured-list players
remain. Organization membership and roster status are checked as of the day the
script runs, independently of the requested statistics dates.

Install the optional Excel dependency once:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-export.txt
```

Choose two CSV files, one Excel workbook with `Batters` and `Pitchers`
worksheets, or both. The through-date controls the final day included. Without
`--start`, the range begins January 1 of the selected season (year-to-date):

```powershell
.venv\Scripts\python.exe export_mlb_ytd.py --season 2026 --through 2026-09-29 --format csv
.venv\Scripts\python.exe export_mlb_ytd.py --season 2026 --through 2026-09-29 --format xlsx
.venv\Scripts\python.exe export_mlb_ytd.py --season 2026 --through 2026-09-29 --format both
```

For a custom range, supply `--start` and `--through` in `YYYY-MM-DD` format.
Both dates are inclusive, must fall within `--season`, and the start must not
follow the end. For example, May 1 through May 30, 2026:

```powershell
.venv\Scripts\python.exe export_mlb_ytd.py --season 2026 --start 2026-05-01 --through 2026-05-30 --format both
```

These are totals for the selected range, not full-season year-to-date totals.
All MLB teams a player appeared for during that range contribute to the totals,
including teams outside the configured pool. The organization column shows the
player's current organization, not the team they played for during the range.
Players without qualifying MLB statistics in the range have no output row.

The exporter writes files under `data/<season>/`. Custom ranges produce
`mlb_hitters_2026-05-01_through_2026-05-30.csv`,
`mlb_pitchers_2026-05-01_through_2026-05-30.csv`, and/or
`mlb_players_2026-05-01_through_2026-05-30.xlsx`. Without `--start`, existing
`*_ytd_<through>` filenames are preserved. The workbook metadata records the
statistics range and roster date; the command also prints both.

If MLB supplies multiple team rows for a player, the exporter uses an explicit
combined total or requests the player's all-team totals. It stops before writing
output if those totals remain ambiguous, rather than duplicating a player or
adding rate statistics. Existing automated tests use mocked API responses;
they do not download MLB data.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```
