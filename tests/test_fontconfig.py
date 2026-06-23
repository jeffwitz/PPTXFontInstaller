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


def test_check_font_accepts_regular_style_suffix_when_base_family_exists(monkeypatch):
    monkeypatch.setattr(fontconfig, "installed_families", lambda: {"noto sans cjk sc"})

    def fake_match(name):
        if name == "Noto Sans CJK SC":
            return "Noto Sans CJK SC", "/fonts/NotoSansCJK-Regular.ttc"
        return "Arimo", "/fonts/Arimo.ttf"

    monkeypatch.setattr(fontconfig, "fc_match", fake_match)

    status = fontconfig.check_font("Noto Sans CJK SC Regular")

    assert status.exact_installed is True
    assert status.resolved_family == "Noto Sans CJK SC"
    assert status.matched_family == "Noto Sans CJK SC"
    assert status.is_substituted is False
    assert status.detection_note is not None


def test_fontconfig_cache_loads_installed_families_once(monkeypatch):
    calls = []
    monkeypatch.setattr(
        fontconfig,
        "installed_families",
        lambda: calls.append("fc-list") or {"arial"},
    )
    monkeypatch.setattr(fontconfig, "fc_match", lambda name: ("Arial", "/fonts/Arial.ttf"))

    cache = fontconfig.FontconfigCache()

    assert cache.is_exact_installed("Arial") is True
    assert cache.is_exact_installed("Arial") is True
    assert calls == ["fc-list"]
