# CLAUDE.md

This is the short handoff note for continuing work on `pptx-font-resolver`.
For a more detailed restart log, read `CODEX.md`.

## Current State

`pptx-font-resolver` is a Python 3.11+ Linux utility for scanning Office
`.pptx` and `.docx` files, extracting font families, checking Fontconfig exact
availability and substitutions, and recommending/installing safe resolutions.

Current user surfaces:

- CLI: `.venv/bin/pptx-font-resolver`
- Qt GUI: `.venv/bin/pptx-font-resolver-gui`

There is no separate Textual/TUI binary at the moment. Earlier "TUI" references
map to the terminal CLI and its Rich tables.

## Development Rules In This Checkout

- Prefix shell commands with `rtk`.
- Keep CLI and GUI behavior aligned when changing resolution or install flows.
- Never install or download fonts during a scan.
- Keep license acceptance explicit. Do not call Fontist with license acceptance
  unless the user selected/confirmed that action.
- After a development change, commit and push to `origin/main`.

## Implemented Features

- Recursive `.pptx` and `.docx` discovery with bounded or infinite depth.
- ZIP/XML parsing without extracting Office files to disk.
- PPTX font extraction from slides, layouts, masters, notes, handouts, charts,
  tables, comments, and theme files.
- DOCX font extraction from document XML, styles, numbering, headers, footers,
  notes, comments, charts, drawings, and theme files.
- PowerPoint and Word theme placeholder resolution.
- Embedded font presence detection in `ppt/fonts/*` and `word/fonts/*`.
- Font aggregation by family, occurrence count, files, and embedded presence.
- Fontconfig exact-install detection, substitution detection, and base-family
  normalization for style suffixes such as `Noto Sans CJK SC Regular`.
- Risk classification for high-risk substitutions, especially symbol fonts and
  CJK fonts substituted by Latin families.
- CLI reports in table, JSON, CSV, and Markdown forms.
- Fontist install commands with dry-run, per-font confirmation, explicit
  license acceptance, user-location installs, `fc-cache`, and post-install
  Fontconfig verification.
- CLI `install-missing --all` mode for one global confirmation before trying
  all missing Fontist-installable fonts.
- Multi-source resolution engine:
  - local Fontconfig status;
  - Fontist exact candidates;
  - Debian/Ubuntu package candidates;
  - Google Fonts exact and curated visual candidates;
  - metric-compatible curated candidates;
  - manual-import recommendations;
  - unsafe symbol-font detection.
- Manual font import for user-owned `.ttf`, `.otf`, and `.ttc` files.
- Live Google Fonts lookup/download through the Google Fonts CSS API, installed
  into the user font area under
  `~/.local/share/fonts/pptx-font-installer/google-fonts`.
- Fontconfig alias persistence for accepted fallbacks:
  - JSON store: `~/.config/pptx-font-resolver/fontconfig-aliases.json`
  - generated Fontconfig file:
    `~/.config/fontconfig/conf.d/90-pptx-font-resolver.conf`
  - `fc-cache -f` refresh after writing aliases.
- Qt GUI:
  - folder picker, depth, jobs, missing-only filter;
  - background scan, install, and resolve workers;
  - install column with a header checkbox to select all visible installable rows;
  - row coloring after Fontist installs: green installed, red unavailable,
    yellow failed;
  - tooltip for Fontist-unavailable rows asking for manual install;
  - multi-source `Resolve all` table;
  - `Explain`, `Install via Fontist`, `Install via Google Fonts`,
    `Install system package`, `Install safe recommendations`,
    `Import font file`, `Accept fallback`, and `Ignore`;
  - JSON/CSV/Markdown export for both scan and resolution views;
  - graceful shutdown of running workers to avoid `QThread` destruction crashes.

## Important Commands

Validate the project:

```bash
rtk .venv/bin/python -m ruff check .
rtk .venv/bin/python -m compileall pptx_font_resolver tests
rtk .venv/bin/python -m pytest -q
```

Launch the GUI:

```bash
rtk .venv/bin/pptx-font-resolver-gui
```

Offscreen GUI smoke test:

```bash
rtk env QT_QPA_PLATFORM=offscreen .venv/bin/python -c 'from PySide6.QtWidgets import QApplication; from pptx_font_resolver.qt_app import _load_qt_modules, build_main_window; app = QApplication([]); window = build_main_window(_load_qt_modules())(); window.show(); print(window.windowTitle()); window.close()'
```

CLI resolution examples:

```bash
rtk .venv/bin/pptx-font-resolver resolve ~/CNRS/Presentations --provider google --format table --jobs 1
rtk .venv/bin/pptx-font-resolver install-missing ~/CNRS/Presentations --provider google --dry-run --jobs 1
rtk .venv/bin/pptx-font-resolver install-missing ~/CNRS/Presentations --provider google --execute --yes --jobs 1
```

Accept a fallback through Fontconfig from CLI:

```bash
rtk .venv/bin/pptx-font-resolver accept-fallback "Futura PT Bold" "Montserrat" --source google-fonts
```

Test without touching real Fontconfig config:

```bash
rtk env XDG_CONFIG_HOME=/tmp/pptx-font-resolver-test .venv/bin/pptx-font-resolver accept-fallback "Futura PT Bold" "Montserrat" --source google-fonts --no-refresh-cache
```

## User Folder Findings

The real folder investigated was `~/CNRS/Presentations`.

Important observed fonts:

- `Futura PT Bold` and `Futura PT Demi` -> Google visual fallback `Montserrat`.
- `ElsevierGulliver` -> Google visual fallback `Source Serif 4`.
- `LegacySans-Bold` -> Google visual fallback `Source Sans 3`.
- `AdvOT...` generated subset-like names -> Google visual fallback `Noto Sans`.
- `Noto Sans CJK SC Regular` is treated as available through the installed base
  family `Noto Sans CJK SC`.

Installed during prior work:

- `Source Sans 3`
- `Source Serif 4`

Already present during verification:

- `Montserrat`
- `Noto Sans`

One real file exceeded the ZIP guard and was reported invalid:

```text
~/CNRS/Presentations/Luis/Présentation HBD A3TS/diapos_A3TS_V2.pptx
archive uncompressed size exceeds limit: 1498762844 > 524288000
```

## Key Files

- `pptx_font_resolver/cli.py`: Typer commands and install orchestration.
- `pptx_font_resolver/qt_app.py`: PySide6 GUI, workers, row coloring, actions.
- `pptx_font_resolver/fontconfig.py`: exact install and substitution checks.
- `pptx_font_resolver/fontist_backend.py`: Fontist wrapper and probe timeout.
- `pptx_font_resolver/scanner.py`: Office discovery and parser orchestration.
- `pptx_font_resolver/pptx_parser.py`: PPTX ZIP/XML extraction.
- `pptx_font_resolver/docx_parser.py`: DOCX ZIP/XML extraction.
- `pptx_font_resolver/resolution/engine.py`: recommendation selection.
- `pptx_font_resolver/resolution/providers.py`: Fontist, distro, Google,
  manual, Fontconfig providers.
- `pptx_font_resolver/resolution/google_fonts.py`: live Google Fonts install.
- `pptx_font_resolver/resolution/manual_import.py`: manual font import.
- `pptx_font_resolver/resolution/fontconfig_aliases.py`: persisted aliases for
  accepted fallbacks.
- `pptx_font_resolver/data/*.json`: curated aliases, distro packages, Google
  family hints, symbol-font risk data.
- `tests/`: 102 focused tests as of this handoff.

## Recent Commits

- `1b374c4 Persist accepted fallbacks with Fontconfig`
- `c876856 Fix Google fallback resolution for presentations`
- `23a0473 Add live Google Fonts installation`
- `1d8e3f2 Expand resolution CdC test coverage`
- `7c95aad Add selected GUI font actions`
- `04ae6a5 Add GUI resolution workflow`
- `79185be Add manual font import CLI`
- `9095ab7 Add multi-source font resolution`

## Last Verification

After the Fontconfig fallback persistence work:

```bash
rtk .venv/bin/python -m ruff check .
rtk .venv/bin/python -m compileall pptx_font_resolver tests
rtk .venv/bin/python -m pytest -q
```

Result: `102 passed`.

## Remaining Work

- Add a GUI management view for accepted Fontconfig fallbacks: list, remove,
  update, and rescan.
- Add a CLI command to list/remove accepted fallback aliases.
- Decide whether `Ignore` should remain session-only or be persisted.
- Add stronger end-to-end GUI tests around real `Resolve all` interactions.
- Consider a true TUI/Textual entry point only if it is still desired; none
  exists now.
- Add more curated mappings for the exact fonts found in real presentation
  folders.
- Add optional LibreOffice round-trip checks: open/resave with embedded fonts
  and verify whether the resolved fallback font is embedded as expected.
- Improve documentation for the real workflow from scan -> resolve -> install
  Google/Open fonts -> accept fallback -> LibreOffice resave/embed.
