from __future__ import annotations

from pathlib import Path

from pptx_font_resolver.models import FontStatus, FontSummary, ScanResult
from pptx_font_resolver.qt_app import font_row, qt_dependency_message, summary_text


def test_qt_dependency_message_mentions_gui_extra():
    assert ".[gui]" in qt_dependency_message()


def test_font_row_formats_status_and_counts():
    font = FontSummary(
        family="Wingdings",
        occurrences=12,
        files=(Path("deck.pptx"),),
        embedded_in=(),
        status=FontStatus(
            requested_family="Wingdings",
            exact_installed=False,
            matched_family="Arimo",
            is_substituted=True,
        ),
        metric_fallbacks=(),
        risk_level="high",
        risk_reason="symbol font substituted",
        recommendation="install_exact_symbol_font_or_check_symbols_manually",
    )

    assert font_row(font) == [
        "Wingdings",
        "high",
        "no",
        "Arimo",
        "12",
        "1",
        "install_exact_symbol_font_or_check_symbols_manually",
    ]


def test_summary_text_counts_high_risk_and_missing_fonts(tmp_path):
    scan = ScanResult(root=tmp_path, documents=(), errors=())
    font = FontSummary(
        family="Wingdings",
        occurrences=1,
        files=(),
        embedded_in=(),
        status=FontStatus("Wingdings", exact_installed=False),
        metric_fallbacks=(),
        risk_level="high",
        risk_reason="symbol font substituted",
        recommendation="install",
    )

    from pptx_font_resolver.analysis import AnalysisResult

    text = summary_text(AnalysisResult(scan=scan, fonts=(font,)))

    assert "Unique fonts: 1" in text
    assert "Missing exact fonts: 1" in text
    assert "High-risk substitutions: 1" in text
