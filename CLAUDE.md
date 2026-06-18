# CLAUDE.md

This file is a handoff note for continuing work on `pptx-font-resolver`.

## Project summary

`pptx-font-resolver` is a Python tool that scans PowerPoint `.pptx` files on
Linux, extracts the fonts used by presentations, checks whether exact fonts are
available through Fontconfig, and reports risky substitutions.

The codebase currently has two user surfaces:

- CLI entry point: `pptx-font-resolver`
- Optional Qt GUI entry point: `pptx-font-resolver-gui`

The GUI and CLI share the same analysis core.

## What has been implemented

- Project scaffold with packaging, tests, Ruff, README, changelog, license, and
  GitHub community files.
- Recursive PPTX discovery with bounded or infinite depth.
- PPTX parsing through ZIP/XML reads without extracting archives to disk.
- Typeface extraction from PowerPoint XML.
- Theme placeholder resolution for common PowerPoint font placeholders:
  `+mn-lt`, `+mj-lt`, `+mn-ea`, `+mj-ea`, `+mn-cs`, and `+mj-cs`.
- Embedded font detection through `ppt/fonts/*`.
- Font aggregation by family, occurrence count, source files, and embedded
  presence.
- Fontconfig checks for exact installation and substitution family.
- Risk classification for dangerous substitutions, especially symbol fonts and
  CJK fonts substituted by Latin families.
- Conservative style suffix normalization, for example detecting
  `Noto Sans CJK SC Regular` as available when `Noto Sans CJK SC` exists.
- JSON, CSV, Markdown, and table report formatting.
- Fontist integration for local user installs:
  - `install-font`
  - `install-missing`
  - dry-run support
  - per-font confirmation
  - Yes / All / No prompt in CLI
  - explicit license acceptance through Fontist only after user confirmation
- Optional PySide6 GUI:
  - folder picker
  - depth and worker controls
  - background scan worker with progress messages
  - missing-only filter
  - table of fonts, risks, Fontconfig matches, occurrences, files, and
    recommendation
  - JSON/CSV/Markdown export
  - row details panel
  - checkboxes for installable fonts
  - `Install selected` button
  - per-font Qt popup with `Yes`, `All`, and `No`
  - background install worker using Fontist in local user location
  - automatic rescan after installation finishes
- Scan robustness improvement: unreadable directories are skipped instead of
  aborting the whole scan.

## Current safety model

No font is installed automatically during a scan.

For Fontist installs, license acceptance is intentionally explicit:

- CLI defaults to accepting a license only for fonts selected through an
  interactive prompt.
- GUI only calls Fontist with license acceptance after the user checks fonts and
  confirms through `Yes` or `All`.
- `install-missing --no-ask` is blocked when license acceptance would otherwise
  happen without per-font confirmation.

Fontist installs are scoped to the user location by default.

## Important files

- `pptx_font_resolver/cli.py`: Typer CLI commands and install prompts.
- `pptx_font_resolver/qt_app.py`: PySide6 GUI and GUI workers.
- `pptx_font_resolver/fontist_backend.py`: Fontist command wrapper.
- `pptx_font_resolver/scanner.py`: PPTX discovery and parsing orchestration.
- `pptx_font_resolver/parser.py`: PPTX ZIP/XML font extraction.
- `pptx_font_resolver/resolver.py`: Fontconfig checks and risk classification.
- `pptx_font_resolver/analysis.py`: shared scan/report analysis entry point.
- `tests/`: focused unit tests for parser, resolver, CLI install behavior,
  Fontist wrapper, scanner, reports, and Qt helpers.

## Development commands

Install for development:

```bash
python -m pip install -e ".[dev]"
python -m pip install -e ".[gui]"
```

Validate changes:

```bash
python -m ruff check .
python -m pytest -q
python -m compileall pptx_font_resolver tests
```

Qt smoke test without opening a visible window:

```bash
QT_QPA_PLATFORM=offscreen python -c 'from PySide6.QtWidgets import QApplication; from pptx_font_resolver.qt_app import _load_qt_modules, build_main_window; app = QApplication([]); window = build_main_window(_load_qt_modules())(); window.show(); print(window.windowTitle())'
```

In this workspace, Codex commands were run through `rtk`, for example:

```bash
rtk .venv/bin/python -m pytest -q
rtk env QT_QPA_PLATFORM=offscreen .venv/bin/python -c '...'
```

## Recent verification

After adding GUI font-install checkboxes and the `Yes | All | No` popup, the
following checks passed:

- `rtk .venv/bin/python -m ruff check .`
- `rtk .venv/bin/python -m pytest -q`
- `rtk .venv/bin/python -m compileall pptx_font_resolver tests`
- `rtk env QT_QPA_PLATFORM=offscreen .venv/bin/python -c '...'`

The latest pushed commit at the time of this note was:

```text
ec4fda0 Add Qt font install selection
```

## Suggested next work

- Add GUI tests around table population and checkbox selection using Qt test
  helpers, not only pure helper tests.
- Add a GUI install dry-run or preview mode so users can see the exact Fontist
  commands before executing them.
- Surface Fontist availability/probe status in the GUI before installation, so
  fonts unavailable through Fontist are visibly disabled or annotated.
- Improve install result reporting in the GUI by showing per-font success/failure
  history instead of only appending text to the summary box.
- Add cancellation support for long scans and long Fontist install batches.
- Add a settings control for install location if user-level Fontist installs are
  not enough in some workflows.
- Add integration fixtures with real-world PPTX edge cases:
  - Symbol / Wingdings / Webdings decks
  - Microsoft Office cloud fonts
  - CJK presentations
  - presentations with embedded fonts
  - unreadable directories in recursive scans
- Document a reproducible Linux setup for Fontist, Fontconfig, and Microsoft
  core fonts where licensing permits it.

## Notes for future agents

- Keep CLI and GUI behavior aligned when changing install or license flows.
- Do not make scan operations install fonts.
- Treat license acceptance as a user-confirmed action tied to selected fonts.
- Keep risky substitution detection conservative; false positives are less
  damaging than silently missing symbol/CJK substitutions.
- Prefer focused tests for each behavior because this project is still small.
