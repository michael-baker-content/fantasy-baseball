# BABBD Roto

A static fantasy baseball tracker for a seven-owner rotisserie league. The site
runs on GitHub Pages; a local Python command downloads completed MLB games and
regenerates the public standings data.

## League setup

- Test league dates: September 1 through September 27, 2026 (inclusive)
- Owners and rosters: copied from the 2025 BABBD playoff workbook for website testing; upcoming fantasy-season rosters have not yet been selected
- Hitting: R, HR, RBI, SB, BB, AVG
- Pitching: W, L, SV, K, ERA, WHIP
- Scoring format: cumulative 6×6; lower L, ERA, and WHIP are better
- Scoring: 7 points for first through 1 point for last; ties split points

League standings count each drafted player's statistics regardless of their
current MLB organization. These rosters are independent of the separate player
exporter's 14-team pool, which remains unchanged.

## Refresh standings

```powershell
.venv\Scripts\python.exe refresh.py
```

Use `--through YYYY-MM-DD` to reproduce a particular day. Completed raw MLB
game feeds are cached in `data/mlb_cache`. Add `--refresh` to redownload them.

To populate the test league with completed games from September 1 through
September 21, 2026, run:

```powershell
.venv\Scripts\python.exe refresh.py --through 2026-09-21
```

This fetches the schedule and any uncached completed game feeds. In-progress
games are excluded; rerun after they finish to include them. The website displays
the September 1–27 league window and the latest completed game date included.
Changing the league window requires this normal refresh, not `--recalculate`,
which only re-scores the statistics already saved in the snapshot.

The command writes `docs/data/league.json`, which the static site reads. Preview
the `docs` folder with any local static web server, then commit and push the
updated JSON when it is ready to publish.

To apply scoring changes to the already saved player statistics without
downloading MLB data, run:

```powershell
.venv\Scripts\python.exe refresh.py --recalculate
```

This updates category points and rankings while preserving the snapshot's
original game dates and data timestamp. Run it before publishing scoring changes.

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
The historical reproduction retains its original 5×5 standings calculation.

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

## Website Player Stats page

The header's **Player Stats** link opens `docs/stats.html`. Its Batters, Pitchers,
IF, OF, SP, and RP tabs support name search, current-team filtering, sortable columns,
and selecting published date ranges. Batters show G, AB, H and the six hitting
categories; pitchers show G, IP and the six pitching categories. Rate statistics
have no qualification minimum. This page uses the exporter's 14-team pool, not
the fantasy owners' rosters or the homepage's test league dates.

Position tabs use the exported MLB primary position: IF includes C, 1B, 2B, 3B,
and SS; OF includes LF, CF, RF, and OF. Generic P pitchers appear in both SP and
RP. SP pitchers with at least two saves in the selected range also appear in RP.
Primary DH players stay in Batters only. Unknown positions remain in the complete
Batters/Pitchers lists. Re-export each published range to add position information
to older website data. Position-rule tests can be run with
`node --test tests/test_stats_positions.cjs`.

Publish regular-season year-to-date data through your chosen date:

```powershell
.venv\Scripts\python.exe export_mlb_ytd.py --season 2026 --through 2026-09-21 --format csv --site
```

This downloads MLB data and writes two local CSV files plus
`docs/data/player-stats.json`. The site's JSON is included by the existing Git
ignore exceptions and must be committed with the page. CSV exports remain
ignored. The page displays a not-yet-published message until its data exists.

To add another selectable range, export it with `--start`, `--through`, and
`--site`. Existing ranges from the same season are retained; rerunning an exact
range replaces it. Year-to-date exports always replace the previous YTD entry.
Exporting a different season starts a new set of ranges. Each range records its
own organization snapshot date, so rerun older ranges if membership needs updating.
Visitors choose among these published ranges; their browsers never call MLB.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```
