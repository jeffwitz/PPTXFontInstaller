from __future__ import annotations

from pptx_font_resolver import fontconfig


def test_check_font_distinguishes_exact_install_from_substitution(monkeypatch):
    monkeypatch.setattr(fontconfig, "installed_families", lambda: {"arial"})
    monkeypatch.setattr(fontconfig, "fc_match", lambda name: ("Carlito", "/fonts/Carlito.ttf"))

    status = fontconfig.check_font("Calibri")

    assert status.exact_installed is False
    assert status.matched_family == "Carlito"
    assert status.is_substituted is True


def test_check_font_marks_exact_family_installed(monkeypatch):
    monkeypatch.setattr(fontconfig, "installed_families", lambda: {"arial"})
    monkeypatch.setattr(fontconfig, "fc_match", lambda name: ("Arial", "/fonts/Arial.ttf"))

    status = fontconfig.check_font("Arial")

    assert status.exact_installed is True
    assert status.is_substituted is False

