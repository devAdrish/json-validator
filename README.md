# JSON Validator

A small desktop GUI app that validates JSON files against a fixed schema (`MainItem`) using [pydantic](https://docs.pydantic.dev/). Built with Tkinter so it runs on Windows and macOS with no external dependencies at runtime.

## What it does

- Opens a JSON file you select.
- Verifies the top-level is an object.
- Requires a top-level `__disclaimer` key.
- Validates every other top-level entry against the `MainItem` schema defined in [validator.py](validator.py).
- Skips any top-level keys whose names start with `__` (treated as metadata).
- Shows results inline:
  - ✅ Green success message if everything matches.
  - ❌ Scrollable list of human-readable errors (location + reason) if anything fails.

## Running from source

Requires Python 3.11+.

```bash
pip install -r requirements.txt
python validator.py
```

## Building standalone binaries

The repo is set up to build with [PyInstaller](https://pyinstaller.org/).

**Windows** (produces `dist/validator.exe`):

```bash
pyinstaller --noconsole --onefile --splash loading.png validator.py
```

**macOS** (produces `dist/validator.app`):

```bash
pyinstaller --windowed validator.py
```

## CI builds

Two GitHub Actions workflows build platform binaries automatically:

- [.github/workflows/build-windows.yml](.github/workflows/build-windows.yml) — builds `validator.exe` on `windows-2022`.
- [.github/workflows/build-macos.yml](.github/workflows/build-macos.yml) — builds `validator.app` on `macos-latest`.

Both run on push to the `release` branch or via manual "Run workflow" dispatch. Artifacts are retained for 30 days under the Actions tab.

### Downloading a build

1. Open the **Actions** tab on GitHub.
2. Pick the workflow (Windows or macOS) and click the latest successful run.
3. Scroll to **Artifacts** at the bottom of the summary page and download the zip.

> macOS note: the `.app` is unsigned. On first launch, right-click → Open, or run `xattr -dr com.apple.quarantine validator.app` to clear the Gatekeeper quarantine flag.

## Project layout

- [validator.py](validator.py) — schema definitions, validation logic, and Tkinter UI.
- [requirements.txt](requirements.txt) — runtime/build dependencies (`pydantic`, `pyinstaller`).
- [loading.png](loading.png) — splash image used by the Windows build.
- [test.json](test.json) — sample input for manual testing.
- [instructions.txt](instructions.txt) — quick reference for the PyInstaller commands.
