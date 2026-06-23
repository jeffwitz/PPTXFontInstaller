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
- `explain`, `import-font`, and `import-fonts` CLI commands for inspecting a
  single font recommendation and importing user-owned `.ttf`, `.otf`, or `.ttc`
  files.
- Optional `font-import` extra for reading font metadata with fontTools.
- GUI `Resolve all`, `Explain`, `Import font file`, and `Install safe
  recommendations` actions backed by the multi-source resolution engine.
- GUI selected-font actions for Fontist installs, single system-package installs,
  fallback acceptance, and ignored recommendations.
- CdC test coverage for resolution-engine core cases, distro package provider
  hints, resolution report formats, and CLI `resolve` filters.
- Live Google Fonts lookup and `install-google-font` support, with GUI
  installation for selected Google Fonts recommendations.
- Google Fonts visual fallbacks for Futura PT, Elsevier Gulliver, LegacySans,
  and generated AdvOT subset names found in presentation decks.

### Changed

- Fontist license acceptance is no longer enabled by default; callers must
  pass `--accept-license` or confirm explicitly in the GUI.
- Reports now include `risk_level` and `risk_reason` fields.
- Fontconfig detection treats unambiguous `Regular` style suffixes as a base
  family lookup fallback.
- Symbol font and CJK-to-Latin substitutions now receive higher-risk
  recommendations.
- Resolution JSON/CSV/Markdown reports now expose the CdC fields for action,
  relation, source, package, install command, license hint, and warnings.
- The GUI now has a resolution-table mode with installed status, Fontist
  availability, recommended action, family, relation, source, risk, and file
  count columns.
- The legacy `fonts` command now shows problematic fonts by default, reserves
  exact installed fonts for `--all-fonts`, and keeps `--only-missing` strict.
- Unknown font families are no longer classified as manual imports unless they
  are present in the curated font data.
- GUI `Resolve all` no longer waits on live Fontist probes; it uses local,
  apt, Google Fonts, and curated fallback data so large folders resolve quickly.
- Fontist availability probes now time out instead of blocking a resolution run.
