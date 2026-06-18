# Changelog

All notable changes to this project will be documented in this file.

The format follows Keep a Changelog, and this project uses semantic versioning.

## [Unreleased]

### Added

- Initial Python package scaffold.
- CLI commands for scanning, font listing, and report generation.
- PPTX ZIP parser with theme placeholder resolution.
- Fontconfig diagnostics and metric-compatible fallback hints.
- Fontist backend wrapper that requires explicit license acceptance.
- GitHub Actions CI, issue templates, and pull request template.
- `install-font` and `install-missing` CLI commands for Fontist-backed local
  user installs.

### Changed

- Reports now include `risk_level` and `risk_reason` fields.
- Fontconfig detection treats unambiguous `Regular` style suffixes as a base
  family lookup fallback.
- Symbol font and CJK-to-Latin substitutions now receive higher-risk
  recommendations.
