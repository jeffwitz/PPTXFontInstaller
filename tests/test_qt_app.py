from __future__ import annotations

from pathlib import Path

from pptx_font_resolver.models import FontStatus, FontSummary, ScanResult
from pptx_font_resolver.qt_app import (
    font_row,
    fontist_unavailable_message,
    install_prompt_text,
    is_installable_font,
    qt_dependency_message,
    summary_text,
)


def test_qt_dependency_message_mentions_gui_extra():
    assert ".[gui]" in qt_dependency_message()


def test_fontist_unavailable_message_uses_fontist_output():
    message = fontist_unavailable_message(
        "Missing Sans",
        "",
        "Font not found locally nor available from Fontist.",
    )

    assert message == "Missing Sans: Font not found locally nor available from Fontist."


def test_fontist_unavailable_message_has_fallback_detail():
    assert (
        fontist_unavailable_message("Missing Sans", "", "")
        == "Missing Sans: not available through Fontist"
    )


def test_install_prompt_mentions_fontist_license_and_font_name():
    message = install_prompt_text("Wingdings")

    assert "Wingdings" in message
    assert "Fontist" in message
    assert "license" in message


def test_is_installable_font_requires_missing_exact_status():
    unknown = FontSummary(
        family="Unknown",
        occurrences=1,
        files=(),
        embedded_in=(),
        status=None,
        metric_fallbacks=(),
        risk_level="unknown",
        risk_reason="unknown",
        recommendation="check",
    )
    missing = FontSummary(
        family="Wingdings",
        occurrences=1,
        files=(),
        embedded_in=(),
        status=FontStatus("Wingdings", exact_installed=False),
        metric_fallbacks=(),
        risk_level="high",
        risk_reason="missing exact font",
        recommendation="install",
    )
    installed = FontSummary(
        family="Arial",
        occurrences=1,
        files=(),
        embedded_in=(),
        status=FontStatus("Arial", exact_installed=True),
        metric_fallbacks=(),
        risk_level="none",
        risk_reason="exact font installed",
        recommendation="none",
    )

    assert is_installable_font(unknown) is True
    assert is_installable_font(missing) is True
    assert is_installable_font(installed) is False


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
