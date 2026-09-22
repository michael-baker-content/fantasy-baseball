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

## Update all site statistics

From the repository root, run this each morning to update through yesterday:

```powershell
.\update.cmd
```

To update again after games finish today:

```powershell
.\update.cmd --today
```

For a specific cutoff, use `.\update.cmd --through 2026-09-21`.
The shortcut uses the repository's `.venv` Python and refreshes standings,
owner pages, YTD Player Stats, and Last 30 Days. It also refreshes player roster
status/IL badges as of the run date. Fixed custom ranges are preserved by the
exporter. CSV exports are generated locally; Excel is not required.

Standings retain the configured league dates and game types and count only final
games. Player Stats retain their separate organization pool and regular-season
scope; `--today` uses whatever statistics the API has published for today, which
may lag completed games. This shortcut does not switch the league to postseason
dates, rosters, or game types; configure those before postseason play.

On a failed step, the shortcut restores both previous site JSON files. Downloaded
cache files and CSV exports may remain. Run only one update at a time. Preview
the results before committing and pushing yourself; the shortcut does neither.

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

The configured category lists determine scoring and homepage column order.
Both normal refreshes and offline recalculation use those lists; unsupported or
duplicate categories are rejected. The historical 2025 reproduction continues
to select its original 5×5 rules explicitly.

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
categories; pitchers show G, IP and the six pitching categories. Qualification
filters default to zero (no minimum). This page uses the exporter's 14-team pool, not
the fantasy owners' rosters or the homepage's test league dates.

IF and OF use the exported MLB primary position: IF includes C, 1B, 2B, 3B,
and SS; OF includes LF, CF, RF, and OF. Primary DHs and unknown positions are
excluded from IF and OF. SP includes players with at least two starts in the
selected range; RP includes players with at least two saves or fewer than two
starts, so players meeting neither original threshold fall into RP. A player
with at least two starts and two saves appears in both, regardless of primary
position. Missing starts data must be refreshed before assigning the fallback
RP group. Games started (GS) is published for filtering without adding a visible
table column. Re-export each published range
to add starts data to older snapshots. Position-rule tests can be run with
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

To publish the last 30 calendar days alongside YTD, run a separate export:

```powershell
.venv\Scripts\python.exe export_mlb_ytd.py --season 2026 --through 2026-09-21 --last-30-days --format csv --site
```

This covers August 23 through September 21 inclusive. `--last-30-days` ends on
`--through`, not the visitor's current date, and cannot be combined with
`--start`. It is bounded to January 1 of the selected season when necessary.
Each run replaces the published `last30` entry while preserving YTD and custom
ranges from that season. Refresh YTD and last-30-days exports with the same
through-date when updating the site; the browser does not advance either range.

Under **Filters**, minimum AB applies to all Batters/IF/OF results, and minimum
IP applies to all Pitchers/SP/RP results, regardless of the sorted column. Both
accept nonnegative whole numbers, use statistics from the selected range, and
persist while switching tabs and ranges. IP comparisons use outs, so 9.2 IP does
not meet a 10-IP minimum. Zero disables the minimum; missing statistics fail an
active minimum. The result count displays the active minimum even when Filters
is closed. Filters run before sorting and pagination; they do not alter exports.

The **Position** dropdown narrows a tab by primary MLB position (for example,
C within IF or CF within OF); SP/RP filters use the same starts/saves rules as
their tabs. Options follow C, 1B, 2B, 3B, SS, LF, CF, RF, DH, SP, RP order, with
only positions relevant to the selected tab included. TWP, P, and generic OF
are not filter options; those players remain eligible for the broader lists. A
selection is retained when available after switching tabs or ranges; otherwise
it resets to All positions. It combines with team, search, and qualification
filters, and the result count shows the selected position when Filters is closed.

Each view initially displays 25 matching players. **Show more** reveals the next
25; changing a tab, range, filter, or sort resets the visible list to 25. The
browser downloads the complete static snapshot once, then filters and paginates
locally. The Pos. column displays the source's primary MLB designation, which
can be P or TWP even though those are not dropdown choices.

Alert-colored IL badges beside names show roster injury status, such as IL-10.
The accessible description includes the roster snapshot date. When the duration
is unavailable, the badge reads IL without inventing a duration. Status is not
an expected return date and updates only on export. Re-export each published
range to add injury fields to older website data; snapshots lacking those fields
display no badge.

Narrow layouts hide supporting statistics (G, AB, H, IP). If the selected sort
column becomes hidden, sorting resets to HR for batting views or K for pitching
views. Selecting a team similarly resets an active Team sort. Long player names
wrap on mobile rather than requiring a hover tooltip. Both pages share saved
theme handling, including when browser storage is unavailable.

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```

Run the JavaScript regression tests with Node.js (no additional packages needed):

```powershell
node --test tests/test_stats_positions.cjs tests/test_ui.cjs
```

These cover position eligibility, hidden-column sorting, theme behavior, and
selected text/focus contrast pairs. They are not a full browser accessibility
audit. Before publishing, preview both themes at narrow and wide widths, use
Tab/Enter/Space to sort the homepage, and check the menu and modal with Escape.
On Player Stats, sort by AB and then narrow below 641px; verify the HR sort
indicator appears. Sort by Team and select one team; verify the visible default
sort is restored. Confirm long player names remain readable on mobile.

## Optional static analysis with Skylos

The local Windows / Python 3.14 development environment uses Skylos 4.37.0 for
static analysis and dead-code detection. Skylos is not required to refresh MLB
data, run the website, or deploy GitHub Pages.

Run the scan from the repository root:

```powershell
.\.venv\Scripts\skylos.exe scan . --no-grep-verify
```

The initial user-run scan reported A+ (100/100) across 16 project files with no
dead code detected. Grep verification was disabled. This describes that scan,
not a guarantee of correctness or a replacement for tests and browser checks.

See [Python-focused Skylos setup](SETUP_SKYLOS.md) for the isolated installation
procedure, compatible MCP constraint, parser stubs, and validation steps.
The procedure is not yet verified on a fresh environment; the existing
`requirements-skylos.txt` remains a snapshot of the original customized setup.
The guide explains its dependency gaps and how to validate a replacement.
