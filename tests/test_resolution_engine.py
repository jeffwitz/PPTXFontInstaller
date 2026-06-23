from __future__ import annotations

from pptx_font_resolver.resolution import default_engine
from pptx_font_resolver.resolution.google_fonts import GoogleFontInfo


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
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.providers.lookup_google_font",
        lambda family, timeout: None,
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


def test_resolution_engine_can_resolve_live_google_font(monkeypatch):
    monkeypatch.setattr(
        "pptx_font_resolver.fontconfig.installed_families",
        lambda: set(),
    )
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.engine.check_font",
        lambda family: None,
    )
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.providers.lookup_google_font",
        lambda family, timeout: GoogleFontInfo(
            family=family,
            css_url=f"https://fonts.googleapis.com/css2?family={family}",
            font_urls=("https://fonts.gstatic.com/s/demo/v1/a.woff2",),
        ),
    )
    engine = default_engine(provider="google")

    resolution = engine.resolve_family("Merriweather")

    assert resolution.recommended_action == "install_google_font"
    assert resolution.recommended_candidate is not None
    assert resolution.recommended_candidate.source == "google-fonts"
    assert resolution.recommended_candidate.install_command == (
        "pptx-font-resolver",
        "install-google-font",
        "Merriweather",
    )
