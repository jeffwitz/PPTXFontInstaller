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
pptx-font-resolver install-font "Aptos" --location user --accept-license
pptx-font-resolver install-missing ./documents --ask --location user
pptx-font-resolver install-missing ./documents --all --location user
pptx-font-resolver-gui
```

No font is downloaded or installed automatically. Fontist installation support
is intentionally interactive and requires explicit license acceptance through
`--accept-license` or a GUI confirmation.

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
- Risk classification for dangerous substitutions, including symbol fonts and
  CJK fonts substituted by Latin families.
- Conservative style-suffix normalization, such as treating
  `Noto Sans CJK SC Regular` as installed when `Noto Sans CJK SC` is present.
- Fontist-backed local user installation commands with dry-run, per-font
  confirmation support, Yes / All / No prompts, and an `--all` mode that tries
  every missing font after one global confirmation and prints a terminal report.
- Optional PySide6 GUI for selecting a folder, scanning in the background,
  reviewing font risk, installing selected fonts or all missing fonts, coloring
  post-install results, and exporting JSON/CSV/Markdown reports.
