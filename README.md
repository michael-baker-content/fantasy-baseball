# Fantasy Baseball League Tracker

Create a postseason fantasy baseball website for your league. The site shows
standings, owner rosters, and searchable player statistics. Download MLB
statistics on your computer, preview the results, and publish them to GitHub
Pages. Visitors do not need Python or a login.

## Set up your own league

### 1. Make your own copy

Fork this repository into your GitHub account and download or clone your copy
to your computer. The included settings and published data are examples;
replace them with your league's information before publishing.

The commands below use Windows PowerShell. Run each command separately from
the project folder. You will need Python; this project is developed with Python
3.14. Create a local Python environment:

```powershell
py -3.14 -m venv .venv
```

Normal website updates and CSV exports use Python's standard library. They do
not require Excel, Skylos, or extra Python packages. Optional test and Excel
dependencies are explained below. On other operating systems, use your
environment's Python executable with the `-m scripts.NAME` commands;
the `.cmd` shortcuts are for Windows.

### 2. Name your league and choose its dates

Open `config/league.json` in a text editor. Keep the JSON punctuation intact
and change these settings:

| Setting | What to enter |
| --- | --- |
| `name` | Your league's name, used in the website header and browser-tab titles. |
| `season` | The MLB season year. |
| `start_date` | The first day your league counts, in `YYYY-MM-DD` format. |
| `end_date` | The last day your league counts, inclusive. |
| `owners` | Your fantasy team owners' names. Replace the example list. |
| `regular_season_end` | The final day of that year's MLB regular season. |
| `phase` | Start with `regular` to collect regular-season player statistics. Switch to `postseason` after saving the final regular-season totals. |
| `game_types` | Keep `F,D,L,W` to count postseason games for standings. |

The phase controls which statistics are refreshed and the default cutoff date.
It does not change the league's dates or game types. While the phase is
`regular`, postseason standings can still be empty and regular-season Player
Stats can still be available.

The default scoring is cumulative 6×6:

- Hitters: R, HR, RBI, SB, BB, AVG.
- Pitchers: W, L, SV, K, ERA, WHIP.

Lower L, ERA, and WHIP are better; higher values are better for the others.
You can select a subset of these supported categories in the `categories` lists
to change scoring and the standings columns. Player Stats and owner tables
still display their built-in statistics. Adding new categories requires code changes.

### 3. Add your owners' players

Edit `config/roster.csv` in a spreadsheet or text editor. Keep the header row
and replace the example players. Each row contains:

| Column | What to enter |
| --- | --- |
| `owner` | An exact match for a name in `config/league.json`. |
| `section` | `hitting` or `pitching`. |
| `slot` | The roster-slot label you want to display. |
| `player_id` | The player's numeric MLB ID, found at the end of their MLB player-page URL. |
| `player_name` | The player's display name. |

Save as CSV UTF-8. There is no fixed owner count or roster size. An owner may
have an empty roster or only hitters or pitchers. A two-way player can have a
separate row in each section. Duplicate players within the same owner's section
are rejected.

Check your configuration without downloading data:

```powershell
.\.venv\Scripts\python.exe -m scripts.refresh --check-config
```

Standings count rostered players regardless of their current MLB organization.

### 4. Choose the Player Stats pool

Player Stats uses a separate list of MLB organizations, not the fantasy rosters.
Edit `PLAYOFF_TEAMS` near the top of `scripts/export_mlb_ytd.py` to choose those
organizations. Use the full MLB team names, following the existing format. This is
currently a setting in the script, rather than a separate configuration file.

For a fresh setup, remove the included `docs/data/player-stats.json` before
your first export so example date ranges are not carried into your league.
Create a regular-season snapshot for your season. This example uses 2026 and
September 27; replace both with your year and desired completed date:

```powershell
.\.venv\Scripts\python.exe -m scripts.export_mlb_ytd --season 2026 --through 2026-09-27 --format csv --site
```

This downloads MLB data. It includes eligible players currently affiliated with
the selected organizations, including optioned and injured-list players.
Released players and free agents are excluded. Statistics include games played
for previous teams, even teams outside the chosen pool.

The exporter verifies roster candidates against each player's current team and
maps minor-league affiliates to their MLB parent organization. An old team's
roster entry alone cannot establish membership. Unresolved affiliations stop
the export rather than publishing guessed assignments.

### 5. Prepare your player review sheet

`config/sheet-players.csv` holds optional draft-sheet selections and manual
position eligibility. For a new league, remove the included example sheet or
move it outside the project before generating your own. Otherwise, the generator
preserves the example selections for matching players.

```powershell
.\sheet.cmd
```

This reads the snapshot you just created without downloading more data. Players
start with `Sheet` set to `No` and their primary position. Leave those defaults
or edit them as described under **Review Sheet players and positions** below.
The update process expects this file to exist.

### 6. Generate and preview your website

With `phase` set to `regular`, run:

```powershell
.\update.cmd
```

This publishes Sheet settings, standings, owner pages, regular-season Player
Stats ranges, and the postseason range. After the regular season, regular-season
statistics are capped at `regular_season_end`. Once those totals are final,
follow the phase-switch instructions below.

Start a local preview:

```powershell
.\.venv\Scripts\python.exe -m http.server 8000 --directory docs
```

Open `http://localhost:8000` in your browser. Check the league name, dates,
owners, rosters, and Player Stats. Press `Ctrl+C` in PowerShell to stop the
server. Refresh the browser after changes; use `Ctrl+F5` if old scripts or styles
appear to be cached.

### 7. Publish to GitHub Pages

Commit and push your configuration and generated website files to your own
repository. In its GitHub Pages settings, choose **Deploy from a branch**,
select your default branch, and select the `/docs` folder.

The site reads committed JSON files in `docs/data/`. GitHub Pages does not run
the Python scripts or refresh statistics for you. After each local update,
preview, commit, and push to publish the new results.

## Update statistics during the season

### Optional automatic postseason updates

The **Update postseason statistics** GitHub Actions workflow targets checks at
:05 and :35 from 1:05 p.m. through 11:05 p.m., plus 11:30 p.m. Pacific.
Explicit UTC schedules cover both daylight and standard time; a runtime check
allows scheduled statistics work only from 1:00–11:30 p.m. Pacific. Extra or
late runs outside that window stop after logging their timing. A delayed final
check past 11:30 p.m. is skipped. Each run's Summary shows the trigger, UTC and
Pacific start times, gate decision, and statistics result. GitHub can delay
scheduled jobs. Games finishing later are picked up at the next scheduled check;
use **Actions → Update postseason statistics → Run workflow** for an earlier check.

To enable it after pushing the workflow and scripts to your default branch:

1. Set **Settings → Pages → Source** to **GitHub Actions**.
2. Allow GitHub Actions in repository settings. Repository rules must allow the
   workflow's token to push generated data to the default branch.
3. Set `phase` to `postseason` and confirm the configured season dates and saved
   regular-season player pool. Push those settings before running the workflow.
4. Run the workflow manually once and inspect its log and deployment result.

The workflow compares completed game IDs with both saved snapshots. It stops
without a commit or deployment when there are no new games. During the first
half hour after 1 p.m., and on
manual runs, it also retrieves fresh completed box scores to detect corrections.
It rebuilds both snapshots from the same feeds, keeping regular-season ranges,
fantasy roster configuration, and Sheet files unchanged. Timestamp-only changes
do not trigger publication. A new included game is recorded even if none of its
players contribute to a fantasy roster.

When data changes, the bot commits only `docs/data/league.json` and
`docs/data/player-stats.json`, then explicitly deploys `docs/` to Pages. You do
not need to push daily statistics yourself. Pull those bot commits before making
local updates. No personal access token is needed. A rejected push stops deployment;
the workflow never force-pushes. If deployment fails after a successful data commit,
use **Re-run all jobs** on that failed run to retry publication.

Updates are limited to the configured postseason window plus one extra day for
late final games/corrections. Outside that window the job exits without MLB
requests. Disable the workflow from its Actions menu when it is no longer needed.
Only the default branch runs this workflow. Website code changes without data
changes do not trigger deployment here; this workflow is for statistics updates.

### Local updates

Run this from the project folder:

```powershell
.\update.cmd
```

- With `phase: "regular"`, the default cutoff is yesterday. Regular-season
  totals and Last 30 Days are updated, capped at `regular_season_end`.
- With `phase: "postseason"`, the default cutoff is today. Completed postseason
  games are updated and regular-season snapshots are left unchanged.
- Both modes publish saved Sheet selections and refresh league standings using
  the configured dates and game types.

Use `--today` to include today's available statistics in regular mode. Use
`--through YYYY-MM-DD` for a specific cutoff. For example:

```powershell
.\update.cmd --through 2026-09-27
```

Standings and postseason Player Stats count completed games only. Regular-season
exports use the API's published daily totals. Run again after games finish to
pick up newly completed postseason games.

Run only one update at a time. If a step fails, the shortcut restores the three
previous website JSON files. Downloaded cache files and CSV exports may remain.
The shortcut never commits or pushes.

### Switch to postseason updates

1. Leave `phase` set to `regular` until the final regular-season games finish.
2. Run `.\update.cmd --through YYYY-MM-DD`, replacing the date with your
   `regular_season_end`, to save final totals and the last 30 calendar days.
3. Change `phase` to `postseason` in `config/league.json`.
4. Use `.\update.cmd` after postseason games finish.

The saved ranges are labeled **Regular Season** with the year and **Last 30
Days - Regular Season**. Last 30 Days means calendar days, not games.
**Postseason** is the default range. A visitor's range choice persists during
their browser-tab session; other filters are not saved between visits.

Postseason Player Stats uses the saved regular-season YTD player pool, including
players without postseason appearances. Organization and injury information
also retains that snapshot's date. Eliminated teams are not automatically
removed. Changing the exporter team list alone does not change an existing
snapshot. Rebuilding YTD changes the pool used by the next postseason update
and replaces the saved regular-season data.

Before your configured opening day, initialize empty postseason displays without
MLB downloads using the command below. The YTD snapshot and Sheet CSV must
already exist:

```powershell
.\update.cmd --prepare
```

### How empty statistics and standings work

Players without an appearance show dashes. An owner's hitting and pitching
totals activate separately: once a hitter appears, hitting counts can show
zeros; pitching still shows dashes until a pitcher appears. Rates with no
denominator remain unavailable.

Owners with appearances rank above owners without appearances. Inactive owners
have no points and tie at the bottom. With N owners, available category results
receive the highest available points on the N-to-1 scale, averaging ties.
Unavailable categories receive no points. Equal total scores share a rank.
Empty owners still count toward N. These appearance rules apply to the
postseason configuration; historical regular-season scoring is unchanged.

## Check one game's status

Run `.\check-game.cmd 123456`, replacing `123456` with the MLB game ID
(`gamePk`). It requests the latest feed without changing website data, Sheet
selections, or cached game feeds. It reports whether MLB marks the game final
and whether batting and pitching box scores are present for both teams.
This does not verify that regular-season date-range totals have updated, or
that later official scoring corrections are impossible.

For postseason games, the same command also checks whether the game was included
in the local Standings/owner totals and Postseason Player Stats. Updates now save
the IDs used in each calculation. Older snapshots report Unknown until refreshed.
Inclusion applies to eligible players in each pool, not every MLB player. This
checks local files, not the deployed website or subsequent scoring corrections.
Postseason totals are calculated directly from completed box scores; they do not
wait for the regular-season date-range endpoint.

The equivalent Python command is
`.\.venv\Scripts\python.exe -m scripts.check_game 123456`.

To check whether regular-season daily totals match the box scores, run:

```powershell
.\check-game.cmd 123456 --verify-totals
```

This uses the exporter's date-range endpoint for the game's official date and
compares hitting AB, H, R, HR, RBI, SB, BB and pitching outs, H, ER, BB, K.
It reports **Daily totals match**, **Totals not yet matching**, or **Unable to
verify**. Doubleheaders are combined; another unfinished game for either team
on that date prevents verification. Missing fields or ambiguous totals also
prevent verification. W/L/SV and every other statistic are not checked.
Matching confirms the checked daily values, not that every season-long query
or the saved website has updated. No files or game caches are changed.
For postseason games this option is not applicable; the normal local inclusion
check still runs because postseason calculations use box scores directly.

## Change your league later

Edit the league name, dates, categories, or owner list in `config/league.json`.
Keep owner names in `config/roster.csv` consistent with that list. Then run the
configuration check and `.\update.cmd`. Configuration edits alone do not change
the published site.

Owner count and roster size do not require code changes. Names must be nonempty
and unique, ignoring case. The check rejects unknown owners, invalid sections
or player IDs, and duplicate entries within an owner's section.

To re-score saved statistics after a category change without downloading data:

```powershell
.\.venv\Scripts\python.exe -m scripts.refresh --recalculate
```

This preserves saved dates and player statistics. Roster or league-window
changes require a normal refresh instead.

To refresh only standings and owner pages:

```powershell
.\.venv\Scripts\python.exe -m scripts.refresh
```

This defaults to today. Add `--through YYYY-MM-DD` for a cutoff or `--refresh`
to download completed game feeds again instead of using the local cache.

## Review Sheet players and positions

Run `.\sheet.cmd` to generate or update `config/sheet-players.csv` from saved
YTD data. Rows are sorted by league, team, last name, and first name. Two-way
players have one row. Keep MLB IDs unchanged.

- **Sheet:** enter `Yes` or `No`. The site's **Sheet Players Only** checkbox
  limits results to Yes players during regular-season mode. In postseason mode,
  the checkbox is hidden and this filter is disabled; manual positions still apply.
- **Positions:** enter a JSON array such as `["CF","RF"]` or `["DH","SP"]`.
  Use `[]` for no assigned positions. All assigned positions appear under Pos.
  and control filters and tab eligibility, even for Sheet=No players.

In Google Sheets, edit the array as normal cell text, then use **File → Download
→ Comma-separated values (.csv)** and replace the local CSV. Sheets handles CSV
quotation marks. Download changes before rerunning the generator so it reads
your latest edits.

The generator preserves existing choices and position arrays, seeds new
players, and saves a `.csv.bak` backup. Daily updates never regenerate this CSV,
run selection estimates, or overwrite manual eligibility. They only publish its
current contents.

After a roster refresh, finish and save any spreadsheet edits before running
`.\sheet.cmd`. It removes players absent from the refreshed YTD pool, updates
team labels, preserves retained players' choices and positions by MLB ID, and
adds new players with Sheet=No. Reopen or reimport that generated CSV before
continuing spreadsheet edits, so an older spreadsheet does not restore removed
rows. The backup contains the previous local CSV, including departed players.

Publish Sheet edits without downloading statistics:

```powershell
.\.venv\Scripts\python.exe -m scripts.publish_sheet
```

Commit both `config/sheet-players.csv` and `docs/data/sheet-players.json` to keep
your review and website in sync.

### Optional selection suggestions

`.\seed-sheet.cmd` creates an initial review with up to 11 hitters and 8 pitchers
per organization marked Yes. It uses saved YTD data and never overwrites an
existing file. To keep suggestions separate:

```powershell
.\seed-sheet.cmd --output config/sheet-suggestions.csv
```

The estimates favor playing time and fantasy contributions:

- Hitters: AB + 8×HR + 12×SB + R + RBI + BB.
- Pitchers: true innings + 0.5×K + 12×SV + 5×W.

These are rough suggestions, not projections. Incidental pitching by position
players is excluded; injured players remain candidates. Review roles and health
yourself. This step is separate from normal generation and daily updates.

## Player Stats behavior

Batters, Pitchers, IF, OF, SP, and RP tabs support search, sorting, team,
owner, position, minimum AB/IP, and Sheet filters. Each view initially shows 25
players; **Show more** reveals another 25. Filtering uses downloaded static
data, with no visitor requests to MLB.

Owner matching uses MLB IDs from the league rosters. An owner's players outside
the selected organization pool will not appear here, even if they appear on
that owner's roster page.

Manual Sheet positions take precedence. Explicit SP/RP assignments grant those
tabs directly. Generic P/TWP assignments use starts and saves in the selected
range: SP requires at least two starts; RP includes pitchers with at least two
saves or fewer than two starts. The same thresholds apply to the original
pitching fallback. Pitchers can qualify for both. Missing starts data does not
imply zero starts. All pitching views exclude incidental pitching by position
players. Pitchers, SP, and RP require a P, SP, RP, or TWP designation, using
manual Sheet positions when present and the source position otherwise.

IF includes C, 1B, 2B, 3B, and SS. OF includes LF, CF, RF, and generic OF;
generic OF does not grant a specific outfield position. Primary DH-only players
remain in Batters. An empty manual array grants no position-tab eligibility.
Players without a Sheet entry use source positions and the existing fallback
rules. Source lists determine who appears under Batters or Pitchers.

Minimum AB applies to batting views and minimum IP to pitching views, regardless
of the sorted column. Zero disables the minimum. Missing statistics fail an
active minimum. Innings are measured in outs, so 9.2 IP does not meet a 10-IP
minimum. ERA and WHIP use underlying totals when available and display three
decimal places.

IL badges show recorded roster status, not an expected return date. Check the
information popup for snapshot dates. Narrow screens hide supporting statistics
and the Owner column. Both pages share the saved light/dark theme.

## Export statistics for other uses

The standalone exporter always retrieves regular-season statistics. Choose
`--format csv` for separate hitter and pitcher files, `xlsx` for a workbook with
Batters and Pitchers worksheets, or `both`.

Excel output needs this optional dependency:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-export.txt
```

Example season-total CSV export; substitute your season and cutoff:

```powershell
.\.venv\Scripts\python.exe -m scripts.export_mlb_ytd --season 2026 --through 2026-09-27 --format csv
```

Example custom range:

```powershell
.\.venv\Scripts\python.exe -m scripts.export_mlb_ytd --season 2026 --start 2026-05-01 --through 2026-05-30 --format both
```

Dates are inclusive and must be within the selected year. Without `--start`,
statistics begin January 1. Files are saved under `data/<season>/`. Statistics
include all teams a player appeared for in the range; the organization column
reflects affiliation when the export runs. Players without qualifying MLB
statistics in that range have no row.

Add `--site` to publish a selectable website range. Existing ranges in the same
season are retained; an exact range is replaced when exported again. A new
season starts a new set of ranges. Each range has its own roster snapshot date.

Use `--last-30-days` instead of `--start` to cover the 30 calendar days ending
on `--through`, bounded to January 1. Each run replaces the `last30` entry.
After freezing regular-season data, avoid exporting those ranges again unless
you intend to replace them.

## Project layout

| Location | Purpose |
| --- | --- |
| `config/` | League settings, fantasy rosters, and manual Sheet choices. |
| `scripts/` | Commands for refreshing, exporting, and publishing data. |
| `mlb/` | Shared API, statistics, and scoring code. |
| `docs/` | The static website served by GitHub Pages. |
| `docs/data/` | Generated website JSON; commit these files to publish updates. |
| `data/` | Local exports and cached MLB feeds. |
| `tests/` | Automated Python and JavaScript checks. |

Run Python entry points from the project folder with `-m scripts.NAME`.
The Windows shortcuts use the project's `.venv` environment. Downloaded
exports, MLB caches, spreadsheet references, virtual environments, and review
backups are ignored by Git, as are personal archives and local assistant settings.
The authoritative Sheet CSV and generated website
JSON are tracked.

## Tests and checks

Install the Python test runner once:

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
```

Run these separately. A unique temporary folder avoids shared Windows
temporary-directory permission problems:

```powershell
$testTemp = Join-Path $env:TEMP ("fantasy-pytest-" + [guid]::NewGuid().ToString())
```

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp="$testTemp"
```

With Node.js installed, run the JavaScript tests; no npm packages are needed:

```powershell
node --test tests/test_stats_positions.cjs tests/test_ui.cjs
```

Tests use saved fixtures or mocked responses and do not download MLB data.
They cover scoring, publication, filtering, and selected interface behavior;
they are not a complete browser accessibility audit. Before publishing, preview
both themes on narrow and wide screens, check owner pages and filters, and use
the keyboard to operate sorting, menus, and dialogs.

### Optional static analysis

Skylos is optional and is not needed to refresh data or run the website.
See [Python-focused Skylos setup](SETUP_SKYLOS.md) for installation details and
limitations. The customized `requirements-skylos.txt` is an environment snapshot,
not the basic website dependency list or a verified fresh-install recipe.

After following that guide, run:

```powershell
.\.venv\Scripts\skylos.exe scan . --no-grep-verify
```
