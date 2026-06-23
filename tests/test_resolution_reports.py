from __future__ import annotations

import csv
import json
from io import StringIO

from pptx_font_resolver.resolution.models import FontCandidate, FontResolution, ResolutionReport
from pptx_font_resolver.resolution.report import to_csv, to_json, to_markdown


def make_resolution(
    family: str,
    action: str,
    relation: str,
    source: str,
    *,
    risk: str = "medium",
) -> FontResolution:
    candidate = FontCandidate(
        requested_family=family,
        provided_family=family if relation == "exact" else f"{family} Fallback",
        source=source,
        relation=relation,
        installable=False,
        confidence=0.5,
    )
    return FontResolution(
        requested_family=family,
        exact_installed=action == "none",
        candidates=(candidate,),
        recommended_candidate=candidate,
        recommended_action=action,
        risk_level=risk,
        notes=(),
    )


def test_resolution_json_contains_recommended_action():
    report = ResolutionReport(
        scanned_files=1,
        requested_fonts=1,
        missing_fonts=1,
        resolved_exact=0,
        resolved_metric=1,
        manual_required=0,
        unsafe=0,
        resolutions=(
            make_resolution(
                "Calibri",
                "install_metric_compatible",
                "metric-compatible",
                "distro-package",
            ),
        ),
    )

    payload = json.loads(to_json(report))

    assert payload["summary"]["requested_fonts"] == 1
    assert payload["resolutions"][0]["recommended_action"] == "install_metric_compatible"


def test_resolution_csv_contains_relation_column():
    report = ResolutionReport(
        scanned_files=1,
        requested_fonts=1,
        missing_fonts=1,
        resolved_exact=0,
        resolved_metric=1,
        manual_required=0,
        unsafe=0,
        resolutions=(
            make_resolution(
                "Calibri",
                "install_metric_compatible",
                "metric-compatible",
                "distro-package",
            ),
        ),
    )

    rows = list(csv.DictReader(StringIO(to_csv(report))))

    assert rows[0]["relation"] == "metric-compatible"
    assert rows[0]["source"] == "distro-package"


def test_resolution_markdown_distinguishes_resolution_types():
    report = ResolutionReport(
        scanned_files=1,
        requested_fonts=5,
        missing_fonts=4,
        resolved_exact=1,
        resolved_metric=1,
        manual_required=2,
        unsafe=1,
        resolutions=(
            make_resolution("Arial", "none", "exact", "local", risk="none"),
            make_resolution(
                "Calibri",
                "install_metric_compatible",
                "metric-compatible",
                "distro-package",
            ),
            make_resolution("Aptos", "use_visual_fallback", "visual-substitute", "curated"),
            make_resolution("Aptos Display", "manual_import", "exact", "manual"),
            make_resolution("Wingdings", "unsafe_symbol_font", "exact", "manual", risk="high"),
        ),
    )

    markdown = to_markdown(report)

    assert "| Arial | none | Arial | exact | local | none |" in markdown
    assert "metric-compatible" in markdown
    assert "visual-substitute" in markdown
    assert "manual_import" in markdown
    assert "unsafe_symbol_font" in markdown
