from __future__ import annotations

from pptx_font_resolver.resolution import default_engine


def test_resolution_engine_cdc_core_cases(monkeypatch):
    monkeypatch.setattr(
        "pptx_font_resolver.fontconfig.installed_families",
        lambda: set(),
    )
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.engine.check_font",
        lambda family: None,
    )
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.providers.fontconfig.check_font",
        lambda family: type("Status", (), {"matched_family": None, "exact_installed": False})(),
    )
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.providers.FontistProvider.candidates_for",
        lambda self, family: (),
    )
    engine = default_engine(provider="all")

    calibri = engine.resolve_family("Calibri")
    cambria = engine.resolve_family("Cambria")
    aptos = engine.resolve_family("Aptos")
    wingdings = engine.resolve_family("Wingdings")
    unknown = engine.resolve_family("UnknownFontXYZ")

    assert calibri.recommended_action == "install_metric_compatible"
    assert calibri.recommended_candidate is not None
    assert calibri.recommended_candidate.provided_family == "Carlito"
    assert calibri.recommended_candidate.relation == "metric-compatible"

    assert cambria.recommended_action == "install_metric_compatible"
    assert cambria.recommended_candidate is not None
    assert cambria.recommended_candidate.provided_family == "Caladea"

    assert aptos.recommended_action == "manual_import"
    assert aptos.recommended_candidate is not None
    assert aptos.recommended_candidate.source == "manual"
    assert any(candidate.relation == "visual-substitute" for candidate in aptos.candidates)

    assert wingdings.recommended_action == "unsafe_symbol_font"
    assert wingdings.risk_level == "high"

    assert unknown.recommended_action == "unresolved"
    assert unknown.recommended_candidate is None
