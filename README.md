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

### Draft sheet review CSV

Run `.\sheet.cmd` to generate `config/sheet-players.csv` from the saved YTD
player pool without downloading data. Columns are League, Team, Last Name,
First Name, MLB ID, Sheet, and Positions, sorted by the first four columns (ignoring accents
and case). Players appearing in both batting and pitching data have one row.
Display names are split after the first word, retaining compound surnames and
suffixes. Sheet defaults to No; edit it to Yes for likely draft picks and save
as CSV UTF-8. Keep MLB IDs unchanged.

Positions contains a JSON array, initially seeded from the saved primary position
(for example `["CF"]`, `["P"]`, or `["TWP"]`). Edit the cell to an array such as
`["1B","OF"]` in Google Sheets, then use File → Download → Comma-separated
values (.csv) to replace `config/sheet-players.csv`. Google Sheets handles CSV
quote escaping. Use `[]` for no
positions. Rerunning the generator preserves existing arrays, including empty
arrays, and seeds only new entries. Publishing applies these arrays to the Pos.
column, position filters, and IF/OF/SP/RP eligibility for all players, including
Sheet=No. Every assigned position is displayed in saved order in every view.
Explicit SP/RP entries grant eligibility directly; P/TWP retains the statistical
starts/saves rules. An empty array grants no position-tab eligibility. Players
without a sheet entry retain the original primary-position/statistical fallback.
The complete Batters/Pitchers lists still require stats in that source and range.
Ohtani's manual `["DH","SP"]` now displays both positions in both lists.

Download your latest Google Sheets edits before rerunning the generator so it
reads the current local CSV. Existing Yes/No selections are retained
for current players, new players default to No, and a `.csv.bak` copy preserves
the previous review, including players who left the pool. The daily update does
not edit this CSV. It publishes its Yes selections to `docs/data/sheet-players.json`.
The unchecked-by-default **Sheet Players Only** checkbox in Player Stats filters
all tabs by those IDs, together with the other filters. Missing IDs default to No.
To publish CSV edits locally without downloading statistics, run:

```powershell
.\.venv\Scripts\python.exe publish_sheet.py
```

Commit the updated site JSON when ready to make the selections live.

### Optional first-pass selections

For an optional one-time first pass before manual review, run `.\seed-sheet.cmd`.
This separate tool leaves `build_sheet.py` unchanged and creates the same review
CSV with up to 11 hitters and 8 pitchers per organization marked Yes. Existing
files are never overwritten; use `.\seed-sheet.cmd --output config/sheet-suggestions.csv`
if you already have a review file. It reads saved YTD data without network access.
Hitter score: AB + 8×HR + 12×SB + R + RBI + BB. Pitcher score:
IP (true innings) + 0.5×K + 12×SV + 5×W. These are rough playing-time and
fantasy-contribution estimates, not projections. Position players' incidental
pitching appearances are excluded from pitcher selection. A two-way player can
fill a slot in both groups but still has only one Yes/No row. Injured players
remain candidates; review health and expected roles manually.

### Daily refresh

The daily refresh publishes only your current CSV Yes/No choices. It never runs
the heuristic, changes those choices, or regenerates the review CSV.

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

On a failed step, the shortcut restores all three previous site JSON files. Downloaded
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

Pitching exports calculate ERA and WHIP from earned runs, hits, walks, and
recorded outs, preserving precision for sorting. The site displays three decimal
places. Zero innings produces an unavailable rate; if calculation inputs are
missing, the exporter retains the API's rate. Re-export existing ranges to apply
this precision to previously saved data.

The header's **Player Stats** link opens `docs/stats.html`. Its Batters, Pitchers,
IF, OF, SP, and RP tabs support name search, current-team filtering, sortable columns,
and selecting published date ranges. Batters show G, AB, H and the six hitting
categories; pitchers show G, IP and the six pitching categories. Qualification
filters default to zero (no minimum). This page uses the exporter's 14-team pool, not
the fantasy owners' rosters or the homepage's test league dates.

Sheet position arrays take precedence. For players without a Sheet assignment,
IF and OF use the exported MLB primary position: IF includes C, 1B, 2B, 3B,
and SS; OF includes LF, CF, RF, and OF. Primary DHs and unknown positions are
excluded from IF and OF. SP includes players with at least two starts in the
selected range; RP includes players with at least two saves or fewer than two
starts, so players meeting neither original threshold fall into RP. A player
with at least two starts and two saves appears in both if designated P, SP, RP,
or TWP. RP excludes position players' incidental pitching appearances and
unknown positions; the complete Pitchers tab retains those records.
Missing starts data must be refreshed before assigning the fallback
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

Under **Filters**, minimum AB is shown only for Batters/IF/OF, and minimum
IP is shown only for Pitchers/SP/RP. Each applies regardless of the sorted column. Both
accept nonnegative whole numbers, use statistics from the selected range, and
persist while switching tabs and ranges. IP comparisons use outs, so 9.2 IP does
not meet a 10-IP minimum. Zero disables the minimum; missing statistics fail an
active minimum. The result count displays the active minimum even when Filters
is closed. Filters run before sorting and pagination; they do not alter exports.

Info buttons beside the minimum labels explain their behavior in a shared dialog.
Only the visible minimum is validated, so an invalid hidden field cannot block
the other player type. Filters use one column below 500px and two at 500px and
above. At 500px and above, Sheet Players Only sits beside the visible minimum,
aligned to the top; below 500px it has its own row.

**Owner Status** offers All Players, Rostered Players, and each of the seven
owners, matched by MLB ID against `docs/data/league.json`. The sortable Owner
column shows Unrostered when there is no match and is hidden at 640px and below.
These are the same test rosters used on Standings, but this page still limits
results to the postseason organization pool. An owner's full roster may therefore
not appear here. Sheet and owner filtering combine with all other filters.

The **Position** dropdown narrows a tab by assigned position (for example,
C within IF or CF within OF); SP/RP filters use the same explicit assignments
and generic-P starts/saves rules as their tabs. OF grants the OF tab without
inventing eligibility at a specific LF/CF/RF position. Options follow C, 1B, 2B, 3B, SS, LF, CF, RF, DH, SP, RP order, with
only positions relevant to the selected tab included. TWP, P, and generic OF
are not filter options; those players remain eligible for the broader lists. A
selection is retained when available after switching tabs or ranges; otherwise
it resets to All positions. It combines with team, search, and qualification
filters, and the result count shows the selected position when Filters is closed.

Each view initially displays 25 matching players. **Show more** reveals the next
25; changing a tab, range, filter, or sort resets the visible list to 25. The
browser downloads the complete static snapshot once, then filters and paginates
locally. Player alphabetical sorting uses last name, then first name, ignoring
case and accents; suffixes break ties after the given name. It also breaks ties
for other sorted columns. Display names remain first-name-first. Compound
surnames are retained using the saved display name's first word as the given name.

Without a Sheet assignment, Pos. displays the source's primary MLB designation. Generic
P becomes SP or RP when eligible for only that group in the selected range;
players eligible for both retain P. Ohtani displays DH in batting views (including
the DH filter) and SP in pitching views; his tab eligibility still follows the
starts/saves rules. Other TWP labels can remain in the complete lists.

Alert-colored IL badges beside names show roster injury status, such as IL-10.
The accessible description includes the roster snapshot date. When the duration
is unavailable, the badge reads IL without inventing a duration. Status is not
an expected return date and updates only on export. Re-export each published
range to add injury fields to older website data; snapshots lacking those fields
display no badge.

Narrow layouts (640px and below) hide supporting statistics (G, AB, H, IP) and Owner. If the selected sort
column becomes hidden, sorting resets to HR for batting views or K for pitching
views. Selecting a team similarly resets an active Team sort. Long player names
wrap on mobile rather than requiring a hover tooltip. Both pages share saved
theme handling, including when browser storage is unavailable.

## Tests

Run these separately; a unique temporary directory avoids the Windows temp-folder
permissions issue encountered during development:

```powershell
$testTemp = Join-Path $env:TEMP ("babbd-pytest-" + [guid]::NewGuid().ToString())
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp="$testTemp"
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
Check 499px, 500px, and desktop filter layouts, both minimum info buttons and
focus return, surname sorting, Sheet/Owner filter combinations, and RP exclusion
of position players. Tests use saved fixtures or mocks and do not fetch MLB data.

Before committing, include the new scripts, tests, `config/sheet-players.csv`,
and `docs/data/sheet-players.json` alongside the website changes. The reviewed
`sheet-players-updated.csv`, suggestions, CSV exports, and backups remain local
and ignored. `sheet-players.csv` is the authoritative selection file.

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
