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

## Tests

```powershell
.venv\Scripts\python.exe -m pytest -q
```
