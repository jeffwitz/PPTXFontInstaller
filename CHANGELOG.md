# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog, and this project uses semantic versioning.

## [Unreleased]

### Added

- Initial Python package scaffold.
- CLI commands for scanning, font listing, and report generation.
- PPTX ZIP parser with theme placeholder resolution.
- DOCX ZIP parser for Word run fonts, styles, headers, footers, notes, comments, and theme fonts.
- Fontconfig diagnostics and metric-compatible fallback hints.
- Fontist backend wrapper that requires explicit license acceptance.
- GitHub Actions CI, issue templates, and pull request template.
- `install-font` and `install-missing` CLI commands for Fontist-backed local
  user installs.
- install-missing now defaults to accepting licenses for explicitly selected
  fonts and uses Yes / All / No prompts.
- Optional PySide6 GUI for folder scanning and report export.
- Mixed PPTX/DOCX folder scanning with document type counts in JSON reports.
- `install-missing --all` to try every missing font after one global license
  confirmation and print a terminal install report.
- GUI `Install all missing` action with post-install row coloring and manual
  install tooltips for fonts unavailable through Fontist.
- `resolve` CLI command with multi-source font-resolution reports for local
  fonts, Fontist, Debian/Ubuntu packages, Google Fonts metadata, curated
  fallbacks, manual imports, and unsafe symbol-font cases.

### Changed

- Fontist license acceptance is no longer enabled by default; callers must
  pass `--accept-license` or confirm explicitly in the GUI.
- Reports now include `risk_level` and `risk_reason` fields.
- Fontconfig detection treats unambiguous `Regular` style suffixes as a base
  family lookup fallback.
- Symbol font and CJK-to-Latin substitutions now receive higher-risk
  recommendations.
