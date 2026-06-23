# CODEX.md

This document is the detailed restart note for continuing work on
`pptx-font-resolver` without reloading the previous Codex session.

Use `CLAUDE.md` for the compact handoff. Use this file when you need the actual
state of the implementation, the latest workflow, and what remains to be built.

## Repository

Path:

```bash
/home/jeff/Code/PPTXFontInstaller
```

Command convention in this workspace:

```bash
rtk <command>
```

Examples:

```bash
rtk git status --short --branch
rtk .venv/bin/python -m pytest -q
```

Branch convention used in the latest work: develop directly on `main`, then
commit and push to `origin/main` at the end of each development step.

## Product Goal

`pptx-font-resolver` helps diagnose and resolve font problems when PowerPoint
or Word files are opened on Linux, especially through LibreOffice.

The tool scans `.pptx` and `.docx` files, extracts font usage from OOXML,
checks exact local availability through Fontconfig, identifies risky
substitutions, and proposes safe resolution actions through several sources:

1. already-installed local fonts;
2. Fontist exact installs;
3. Debian/Ubuntu packages;
4. Google Fonts exact or open visual substitutes;
5. metric-compatible replacements;
6. manual import for user-owned font files;
7. Fontconfig aliases for accepted fallbacks;
8. unresolved/manual handling for unsafe or proprietary cases.

The guiding rule is traceability: a recommendation must say what it will do,
where the font comes from, and whether it is exact, metric-compatible, visual,
generic, or unsafe.

## Current User Surfaces

There are two installed entry points:

```bash
.venv/bin/pptx-font-resolver
.venv/bin/pptx-font-resolver-gui
```

There is no separate Textual/TUI application yet. Earlier "TUI" language should
be interpreted as the Rich terminal CLI unless a future task explicitly asks for
a real TUI.

Current CLI commands:

```text
scan
fonts
report
resolve
explain
import-font
import-fonts
install-google-font
accept-fallback
install-font
install-missing
```

## Safety and License Model

Scanning never installs fonts.

Fontist:

- `install-font` and `install-missing` do not accept licenses by default.
- `--accept-license` is explicit.
- GUI Fontist installation asks before installing selected fonts.
- `install-missing --no-ask` is blocked when it would accept licenses without
  per-font confirmation.

Google Fonts:

- only uses Google Fonts CSS metadata and downloaded font URLs from that
  official flow;
- installs into the user font area under
  `~/.local/share/fonts/pptx-font-installer/google-fonts`;
- refreshes Fontconfig cache after installation unless disabled in code paths.

Manual import:

- only imports `.ttf`, `.otf`, and `.ttc` files already owned/provided by the
  user;
- does not modify font files;
- optionally copies or symlinks into a user font directory and refreshes
  Fontconfig.

Fontconfig accepted fallbacks:

- do not modify Office documents;
- do not install any font;
- create a user-level Fontconfig alias so the requested family resolves to the
  chosen installed fallback family.

## Current Architecture

Core modules:

- `pptx_font_resolver/scanner.py`
  discovers Office files, applies depth and ZIP safety guards, and coordinates
  parser execution.
- `pptx_font_resolver/pptx_parser.py`
  extracts PowerPoint fonts from ZIP/XML entries without full extraction.
- `pptx_font_resolver/docx_parser.py`
  extracts Word fonts from document XML, styles, numbering, headers, footers,
  comments, notes, charts, drawings, and theme data.
- `pptx_font_resolver/fontconfig.py`
  wraps `fc-list` and `fc-match`; distinguishes exact install from Fontconfig
  substitution; strips conservative style suffixes such as `Regular`.
- `pptx_font_resolver/resolver.py`
  builds the older font report with risk classification.
- `pptx_font_resolver/analysis.py`
  shared scan/report entry point for CLI and GUI.
- `pptx_font_resolver/report.py`
  non-resolution JSON/CSV/Markdown output.
- `pptx_font_resolver/fontist_backend.py`
  probes and installs with Fontist; includes probe timeout and optional
  `fc-cache`.

Resolution package:

- `pptx_font_resolver/resolution/models.py`
  defines `FontCandidate`, `FontResolution`, and `ResolutionReport`.
- `pptx_font_resolver/resolution/engine.py`
  ranks provider candidates and chooses the recommended action.
- `pptx_font_resolver/resolution/providers.py`
  implements local, Fontist, distro package, Google Fonts, manual, curated, and
  Fontconfig candidates.
- `pptx_font_resolver/resolution/google_fonts.py`
  performs live Google Fonts lookup and user-local installation.
- `pptx_font_resolver/resolution/manual_import.py`
  reads family metadata and imports user-owned font files.
- `pptx_font_resolver/resolution/fontconfig_aliases.py`
  persists accepted fallbacks through user Fontconfig aliases.
- `pptx_font_resolver/resolution/report.py`
  renders resolution reports as table, JSON, CSV, and Markdown.

Data files:

- `pptx_font_resolver/data/font_aliases.json`
  curated exact/metric/visual fallback mapping.
- `pptx_font_resolver/data/distro_packages.json`
  Debian/Ubuntu package hints.
- `pptx_font_resolver/data/google_fonts_index.json`
  curated Google Fonts fallback hints.
- `pptx_font_resolver/data/symbol_fonts.json`
  unsafe symbol-font list and notes.

GUI:

- `pptx_font_resolver/qt_app.py`
  contains the PySide6 UI, scan/install/resolve workers, row coloring, actions,
  and export buttons.

Tests:

- all tests live in `tests/`;
- there are no separate shell scripts in `tests/`;
- GUI behavior is tested through `tests/test_qt_app.py`, including offscreen
  Qt windows.

## Implemented Scanner and Analysis Behavior

Implemented:

- `.pptx` and `.docx` discovery;
- depth support with integer depth or `infinite`;
- parallel scan jobs;
- invalid/unreadable documents reported without aborting the scan;
- ZIP safety guard to avoid pathological archives;
- no full extraction of Office archives to disk;
- embedded font entry detection;
- PowerPoint and Word theme resolution;
- family aggregation across files.

Important real-world guard observed in `~/CNRS/Presentations`:

```text
archive uncompressed size exceeds limit: 1498762844 > 524288000
```

This affected:

```text
~/CNRS/Presentations/Luis/Présentation HBD A3TS/diapos_A3TS_V2.pptx
```

It is treated as an invalid/guarded document, not a crash.

## Implemented CLI Behavior

General report commands:

```bash
rtk .venv/bin/pptx-font-resolver scan ./documents --depth infinite
rtk .venv/bin/pptx-font-resolver fonts ./documents --all-fonts --show-files
rtk .venv/bin/pptx-font-resolver report ./documents --format json --output report.json
```

Multi-source resolution:

```bash
rtk .venv/bin/pptx-font-resolver resolve ./documents --provider all --format table
rtk .venv/bin/pptx-font-resolver resolve ./documents --provider google --format json
rtk .venv/bin/pptx-font-resolver explain "Futura PT Bold" --provider all
```

Fontist:

```bash
rtk .venv/bin/pptx-font-resolver install-font "Aptos" --location user
rtk .venv/bin/pptx-font-resolver install-font "Aptos" --location user --accept-license
rtk .venv/bin/pptx-font-resolver install-missing ./documents --ask --location user
rtk .venv/bin/pptx-font-resolver install-missing ./documents --all --location user
```

APT / Google guided installs from resolution output:

```bash
rtk .venv/bin/pptx-font-resolver install-missing ./documents --provider apt --dry-run
rtk .venv/bin/pptx-font-resolver install-missing ./documents --provider google --dry-run
rtk .venv/bin/pptx-font-resolver install-missing ./documents --provider google --execute --yes
```

Google Fonts single-family install:

```bash
rtk .venv/bin/pptx-font-resolver install-google-font "Merriweather" --dry-run
rtk .venv/bin/pptx-font-resolver install-google-font "Source Serif 4"
```

Manual import:

```bash
rtk .venv/bin/pptx-font-resolver import-font ~/Downloads/Aptos.ttf
rtk .venv/bin/pptx-font-resolver import-fonts ~/Downloads/fonts --dry-run
```

Accepted fallback via Fontconfig:

```bash
rtk .venv/bin/pptx-font-resolver accept-fallback "Futura PT Bold" "Montserrat" --source google-fonts
```

That command writes:

```text
~/.config/pptx-font-resolver/fontconfig-aliases.json
~/.config/fontconfig/conf.d/90-pptx-font-resolver.conf
```

and runs:

```bash
fc-cache -f
```

Safe temporary test without touching the real user config:

```bash
rtk env XDG_CONFIG_HOME=/tmp/pptx-font-resolver-test .venv/bin/pptx-font-resolver accept-fallback "Futura PT Bold" "Montserrat" --source google-fonts --no-refresh-cache
```

## Implemented GUI Behavior

Launch:

```bash
rtk .venv/bin/pptx-font-resolver-gui
```

Scan view:

- choose folder;
- choose depth;
- choose number of jobs;
- filter to missing fonts;
- table with install checkbox, font, risk, exact status, Fontconfig match,
  occurrences, files, and recommendation;
- header checkbox above install column selects all visible installable rows;
- row details panel;
- JSON/CSV/Markdown export.

Fontist install view behavior:

- `Install selected`;
- `Install all missing`;
- popup with per-font confirmation and Yes / All / No flow;
- background worker;
- rescan after install;
- green rows for installed fonts;
- red rows for fonts unavailable through Fontist;
- yellow rows for Fontist install failures;
- unavailable Fontist row tooltip says the font is not installable through
  Fontist and must be installed manually.

Resolution view:

- `Resolve all` uses the multi-source engine;
- Fontist probing is skipped in the GUI resolve worker by default to avoid long
  blocking probes, but Fontist-specific install remains available;
- table columns:
  - `Family`
  - `Installed`
  - `Fontist`
  - `Recommended action`
  - `Recommended family`
  - `Relation`
  - `Source`
  - `Risk`
  - `Files`
- actions:
  - `Explain`
  - `Install via Fontist`
  - `Install via Google Fonts`
  - `Install system package`
  - `Install safe recommendations`
  - `Import font file`
  - `Accept fallback`
  - `Ignore`

`Accept fallback` behavior:

- takes the selected resolution row;
- finds the recommended fallback candidate;
- writes a user Fontconfig alias from requested family to recommended family;
- refreshes Fontconfig cache;
- marks the family as accepted in GUI state;
- colors the row green;
- shows the config path in the details panel.

Example:

```text
Futura PT Bold -> Montserrat
```

becomes a Fontconfig alias in:

```text
~/.config/fontconfig/conf.d/90-pptx-font-resolver.conf
```

`Ignore` behavior:

- currently session-only;
- it only greys the row in the GUI session;
- it does not write config and does not modify documents.

Worker shutdown:

- running scan/install/resolve workers are stopped defensively on app close;
- this was added after reproducing a Qt abort:
  `QThread: Destroyed while thread '' is still running`.

## Google Fonts and Real Presentation Folder State

The folder investigated during the latest work:

```bash
~/CNRS/Presentations
```

Useful commands for this folder:

```bash
rtk .venv/bin/pptx-font-resolver fonts ~/CNRS/Presentations --format json --show-files --jobs 1
rtk .venv/bin/pptx-font-resolver resolve ~/CNRS/Presentations --provider google --format table --jobs 1
rtk .venv/bin/pptx-font-resolver install-missing ~/CNRS/Presentations --provider google --dry-run --jobs 1
rtk .venv/bin/pptx-font-resolver install-missing ~/CNRS/Presentations --provider google --execute --yes --jobs 1
```

Observed unresolved/problem families and current fallback mapping:

```text
AdvOT... generated subset-like names -> Noto Sans
ElsevierGulliver -> Source Serif 4
Futura PT Bold -> Montserrat
Futura PT Demi -> Montserrat
LegacySans-Bold -> Source Sans 3
Noto Sans CJK SC Regular -> installed base family Noto Sans CJK SC
```

Google/Open fonts installed during the work:

```text
Source Sans 3
Source Serif 4
```

Fonts already present during verification:

```text
Montserrat
Noto Sans
```

After those installs, `install-missing --provider google --dry-run` reports no
remaining Google-installable action for that folder because the recommended
fallback families are already installed.

## What "Accept Fallback" Means Technically

It does not rewrite the `.pptx` or `.docx`.

It configures the local Linux font resolver:

```xml
<alias>
  <family>Futura PT Bold</family>
  <prefer>
    <family>Montserrat</family>
  </prefer>
</alias>
```

Practical consequence:

1. the Office document still asks for `Futura PT Bold`;
2. Fontconfig resolves that family to `Montserrat`;
3. LibreOffice should render with the fallback family;
4. if LibreOffice then saves with font embedding enabled, it should normally
   embed the resolved/used open font, subject to LibreOffice behavior and font
   embedding permissions.

Important nuance: the document XML may still contain the original family name.
The fallback is a local rendering policy, not a document-level substitution.

## Verification Commands

Full validation:

```bash
rtk .venv/bin/python -m ruff check .
rtk .venv/bin/python -m compileall pptx_font_resolver tests
rtk .venv/bin/python -m pytest -q
```

Expected current test count after the latest Fontconfig alias work:

```text
102 passed
```

CLI help:

```bash
rtk .venv/bin/pptx-font-resolver --help
```

GUI smoke test without opening a visible window:

```bash
rtk env QT_QPA_PLATFORM=offscreen .venv/bin/python -c 'from PySide6.QtWidgets import QApplication; from pptx_font_resolver.qt_app import _load_qt_modules, build_main_window; app = QApplication([]); window = build_main_window(_load_qt_modules())(); window.show(); print(window.windowTitle()); window.close()'
```

No dedicated TUI test exists because no dedicated TUI exists.

## Recent Commits To Know

Latest implementation series:

```text
1b374c4 Persist accepted fallbacks with Fontconfig
c876856 Fix Google fallback resolution for presentations
23a0473 Add live Google Fonts installation
1d8e3f2 Expand resolution CdC test coverage
7c95aad Add selected GUI font actions
04ae6a5 Add GUI resolution workflow
79185be Add manual font import CLI
9095ab7 Add multi-source font resolution
```

The worktree should be clean after each completed development step:

```bash
rtk git status --short --branch
```

## Current Gaps and Recommended Next Work

High priority:

- Add GUI management for accepted Fontconfig fallbacks:
  - list all aliases managed by the tool;
  - remove an alias;
  - update an alias;
  - run `fc-cache -f`;
  - rescan/refresh the table.
- Add CLI equivalents:
  - `list-fallbacks`;
  - `remove-fallback`;
  - maybe `clear-fallbacks`.
- Decide whether `Ignore` should remain GUI-session-only or be persisted in a
  user config file.
- Add documentation to README for the new fallback workflow.

Medium priority:

- Add a real end-to-end GUI test for `Resolve all` on generated fixtures.
- Add a GUI test around `Install via Google Fonts` with mocked download.
- Add more curated mappings for real proprietary or embedded-subset family
  names found in `~/CNRS/Presentations`.
- Add import/export of resolution decisions so a reviewed folder can be resumed.
- Improve report output to include accepted Fontconfig aliases.
- Add a safer UI warning for high-risk symbol-font substitutions before allowing
  fallback acceptance.

Optional/future:

- Build a real TUI if still needed. A Textual app would be a new entry point.
- Implement a cache/index if repeated huge-folder scans become too slow.
- Add LibreOffice integration tests:
  - open a presentation;
  - render or save;
  - enable font embedding;
  - inspect the saved PPTX for embedded font entries.
- Add a `loffice` helper workflow for "resave with embedded fonts" once the
  Fontconfig fallback policy is accepted.

## Known Design Decisions

- Keep Fontconfig aliasing separate from document rewriting.
- Prefer user-level files over system-level config.
- Prefer official/open font sources over scraping.
- Treat metric-compatible and visual substitutes as different risk classes.
- Keep symbol fonts conservative and high risk unless exact fonts are available.
- Avoid long Fontist probes in GUI `Resolve all`; use explicit Fontist actions
  where the user selected a font.
- Use Google Fonts for installable open fonts and curated visual substitutes,
  not as a universal answer for proprietary family names.

## If You Resume From Here

Recommended first commands:

```bash
rtk git status --short --branch
rtk git log --oneline -8
rtk .venv/bin/python -m pytest -q
```

If the user asks about the GUI:

```bash
rtk .venv/bin/pptx-font-resolver-gui
```

If the user asks about `~/CNRS/Presentations`:

```bash
rtk .venv/bin/pptx-font-resolver resolve ~/CNRS/Presentations --provider google --format table --jobs 1
```

If the user asks whether a fallback is now active:

```bash
rtk fc-match "Futura PT Bold"
rtk sed -n '1,220p' ~/.config/fontconfig/conf.d/90-pptx-font-resolver.conf
```

If you change code, run validation, commit, and push.
