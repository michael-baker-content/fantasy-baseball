# Python-focused Skylos setup on Windows

Skylos provides optional static analysis and dead-code detection. It is not a
runtime dependency of the BABBD website or MLB refresh scripts.

The existing Python 3.14 environment successfully ran Skylos 4.37.0 and reported
A+ (100/100) across 16 files, with grep verification disabled. The fresh-install
procedure below has **not yet been executed or validated**. It corrects the
known dependency mismatch without modifying the working `.venv` environment.

## Why customize the installation?

Skylos declares parsers for several languages this Python workflow does not use.
The initial Windows installation encountered compiler requirements for these
packages. This setup omits those parsers and installs Skylos separately with
`--no-deps`, while allowing pip to resolve the selected dependencies normally.

Some retained dependencies also contain native code. The install commands use
`--only-binary=:all:` to require prebuilt wheels and avoid local compilation.
If a compatible wheel is unavailable, installation stops; this procedure does
not guarantee availability of every dependency on every Windows architecture.

## 1. Create a separate environment

Run each command block separately in PowerShell, from the repository root.
No environment activation is required. Keep the existing `.venv` unchanged.

```powershell
py -3.14 -m venv .venv-skylos
```

```powershell
.\.venv-skylos\Scripts\python.exe -m pip install --upgrade pip
```

## 2. Install the selected dependencies

These direct dependencies are based on the installed Skylos 4.37.0 package
metadata. The MCP constraint selects a compatible 1.x release rather than
assuming a particular unverified version exists. `keyring` and `pyperclip`
are explicitly included.

```powershell
.\.venv-skylos\Scripts\python.exe -m pip install --only-binary=:all: "inquirer>=3.1.0" "libcst>=1.8.2" "rich>=14.0.0" "textual>=1.0.0" "keyring>=25.6.0,!=3.4.2" requests "tree-sitter>=0.25.2,<0.27" "tree-sitter-typescript>=0.23.2,<0.24" PyYAML networkx pyperclip "ca9>=0.1.1" "mcp>=1.0.0,<2"
```

Install the pinned Skylos package without pulling in its omitted language parsers:

```powershell
.\.venv-skylos\Scripts\python.exe -m pip install --only-binary=:all: --no-deps "skylos==4.37.0"
```

Do not substitute a normal `pip install skylos` or install the current
`requirements-skylos.txt` here: dependency resolution would request the omitted
parsers again, and the current snapshot contains an incompatible MCP 2.x pin.

## 3. Create the import stubs

These commands target the new environment explicitly. Run the variable assignment
first, then the loop. They create only missing directories and empty
`__init__.py` files; existing parser files are never overwritten.

```powershell
$skylosSitePackages = (Resolve-Path -LiteralPath '.\.venv-skylos\Lib\site-packages').Path
```

```powershell
foreach ($parserName in @('tree_sitter_java', 'tree_sitter_go', 'tree_sitter_php', 'tree_sitter_rust')) { $parserDirectory = Join-Path $skylosSitePackages $parserName; if (-not (Test-Path -LiteralPath $parserDirectory)) { New-Item -ItemType Directory -Path $parserDirectory | Out-Null }; $parserInit = Join-Path $parserDirectory '__init__.py'; if (-not (Test-Path -LiteralPath $parserInit)) { New-Item -ItemType File -Path $parserInit | Out-Null } }
```

The stubs satisfy imports only; Java, Go, PHP, and Rust analysis is unavailable.
The Dart parser is also omitted; the inspected version handles its absence.
The installed TypeScript parser is retained for initialization, but this guide
does not establish coverage or correctness for non-Python analysis.

Stub packages do not satisfy pip's distribution requirements. This is a
version-specific workaround, not an upstream-supported minimal installation.
Recheck it before upgrading Skylos.

## 4. Validate the new setup

Inspect dependency consistency:

```powershell
.\.venv-skylos\Scripts\python.exe -m pip check
```

Missing-distribution messages for the intentionally omitted Java, Go, PHP,
Rust, and Dart parser packages are expected and may produce a nonzero exit.
Any other missing dependency or version conflict needs investigation.

Run the same scan used successfully in the original environment:

```powershell
.\.venv-skylos\Scripts\skylos.exe scan . --no-grep-verify
```

`--no-grep-verify` disables a follow-up verification pass that can rescue
false-positive dead-code findings. It does **not** bypass installation,
compilation, or startup imports. We retain it to match the previously successful
local scan, not because omitting parsers inherently requires it.

For the existing working environment, the equivalent command remains:

```powershell
.\.venv\Scripts\skylos.exe scan . --no-grep-verify
```

Review the files analyzed, findings, and errors before comparing grades. A clean
scan is not a substitute for automated tests or browser/accessibility checks.

## Requirements snapshot and reproducibility

The current `requirements-skylos.txt` is a snapshot of the original development
environment, including pytest and openpyxl. It pins `mcp==2.2.0`, whereas Skylos
4.37.0 requires `mcp>=1.0.0,<2`, and omits declared dependencies `keyring` and
`pyperclip`. It has been preserved as a record, not silently rewritten to claim
an installation that has not been tested.

After the separate environment passes the checks above, capture its resolved
versions in a new file:

```powershell
.\.venv-skylos\Scripts\python.exe -m pip freeze | Set-Content -LiteralPath requirements-skylos-validated.txt -Encoding utf8
```

That snapshot still does not contain the stubs. To test an exact replay in
another fresh environment, install the validated snapshot using `--no-deps`
and `--only-binary=:all:`, recreate the stubs, and repeat dependency inspection
and scanning. Only after that replay succeeds should the new snapshot replace
`requirements-skylos.txt` and this guide be marked verified. Record the Python
patch version, Windows architecture, and scan results with that validation.
