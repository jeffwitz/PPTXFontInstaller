# pptx-font-resolver

`pptx-font-resolver` scans PowerPoint `.pptx` and Word `.docx` files on Linux and reports which
fonts they use, whether those fonts are installed exactly, and which Fontconfig
substitutions or metric-compatible fallbacks are available.

The first target is reliable CLI behavior for large folders of Office documents.
The optional Qt GUI reuses the same Python analysis core as the CLI.

## Install for development

```bash
python -m pip install -e ".[dev]"
python -m pip install -e ".[gui]"  # optional Qt GUI
```

## Commands

```bash
pptx-font-resolver scan ./documents --depth infinite
pptx-font-resolver fonts ./documents --all-fonts --show-files
pptx-font-resolver report ./documents --format json --output report.json
pptx-font-resolver resolve ./documents --provider all --format markdown
pptx-font-resolver explain "Calibri"
pptx-font-resolver import-font ~/Downloads/Aptos.ttf
pptx-font-resolver import-fonts ~/Downloads/fonts --dry-run
pptx-font-resolver install-font "Aptos" --location user --accept-license
pptx-font-resolver install-missing ./documents --ask --location user
pptx-font-resolver install-missing ./documents --all --location user
pptx-font-resolver install-missing ./documents --provider apt --dry-run
pptx-font-resolver-gui
```

No font is downloaded or installed automatically. Fontist installation support
is intentionally interactive and requires explicit license acceptance through
`--accept-license` or a GUI confirmation.

## Fonts not available through Fontist

Fontist is only one source. Some Office fonts are proprietary, absent from
Fontist, or unsafe to replace automatically. `resolve` and `explain` combine
Fontist, local Fontconfig data, Debian/Ubuntu package hints, curated
metric-compatible replacements, visual fallback advice, and manual-import
warnings.

Metric-compatible replacements such as Carlito for Calibri and Caladea for
Cambria reduce layout changes but are still substitutions. Visual fallbacks do
not guarantee identical line breaks. Symbol fonts such as Wingdings are marked
high risk because glyph meanings can change.

Manual import is available for users who already have the legal right to use a
`.ttf`, `.otf`, or `.ttc` file:

```bash
python -m pip install -e ".[font-import]"
pptx-font-resolver import-font ~/Downloads/Aptos.ttf
```

This tool does not redistribute proprietary fonts. License acceptance is never
automatic unless explicitly requested by the user.

## Current scope

- recursive `.pptx` and `.docx` discovery with bounded or infinite depth;
- ZIP-based OOXML parsing without extracting archives to disk;
- fast `typeface="..."` extraction from relevant PowerPoint XML entries;
- Word `w:rFonts` extraction from document, styles, numbering, headers, footers, notes, comments, charts, and drawings;
- theme placeholder resolution for PowerPoint placeholders and Word theme fonts;
- embedded font presence detection through `ppt/fonts/*` and `word/fonts/*`;
- aggregate table, JSON, CSV, and Markdown reporting primitives;
- Fontconfig status checks and metric-compatible fallback hints.
- Multi-source resolution reports covering local fonts, Fontist availability,
  Debian/Ubuntu packages, Google Fonts metadata, curated fallbacks, manual
  import advice, and unsafe symbol-font cases.
- Manual `.ttf`, `.otf`, and `.ttc` import commands with font family metadata
  checks and optional Fontconfig cache refresh.
- Risk classification for dangerous substitutions, including symbol fonts and
  CJK fonts substituted by Latin families.
- Conservative style-suffix normalization, such as treating
  `Noto Sans CJK SC Regular` as installed when `Noto Sans CJK SC` is present.
- Fontist-backed local user installation commands with dry-run, per-font
  confirmation support, Yes / All / No prompts, and an `--all` mode that tries
  every missing font after one global confirmation and prints a terminal report.
- Optional PySide6 GUI for selecting a folder, scanning in the background,
  reviewing font risk, installing selected fonts or all missing fonts, coloring
  post-install results, resolving missing fonts through the multi-source engine,
  explaining recommendations, importing user-owned font files, installing safe
  system-package recommendations after confirmation, and exporting
  JSON/CSV/Markdown reports.
