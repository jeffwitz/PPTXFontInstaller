from __future__ import annotations

from pptx_font_resolver.models import FontStatus
from pptx_font_resolver.resolver import classify_risk, recommend_action


def test_symbol_font_substitution_is_high_risk():
    status = FontStatus(
        requested_family="Wingdings",
        exact_installed=False,
        matched_family="Arimo",
        is_substituted=True,
    )

    level, reason = classify_risk("Wingdings", status, False, ())

    assert level == "high"
    assert "symbol" in reason
    assert (
        recommend_action(status, False, ())
        == "install_exact_symbol_font_or_check_symbols_manually"
    )


def test_cjk_font_substituted_by_latin_family_is_high_risk():
    status = FontStatus(
        requested_family="DengXian",
        exact_installed=False,
        matched_family="Arimo",
        is_substituted=True,
    )

    level, reason = classify_risk("DengXian", status, False, ())

    assert level == "high"
    assert reason == "CJK font substituted by a Latin family"
    assert (
        recommend_action(status, False, ())
        == "install_cjk_font_or_select_cjk_compatible_substitute"
    )
