from __future__ import annotations

import json

from conftest import make_pptx, slide_xml
from typer.testing import CliRunner

from pptx_font_resolver.cli import app
from pptx_font_resolver.models import FontStatus


def patch_fontconfig(monkeypatch):
    monkeypatch.setattr(
        "pptx_font_resolver.fontconfig.installed_families",
        lambda: {"arial"},
    )

    def fake_check_font(family: str) -> FontStatus:
        if family == "Arial":
            return FontStatus(family, exact_installed=True, matched_family="Arial")
        return FontStatus(family, exact_installed=False, matched_family=None)

    monkeypatch.setattr("pptx_font_resolver.resolution.engine.check_font", fake_check_font)


def test_cli_resolve_json(tmp_path, monkeypatch):
    patch_fontconfig(monkeypatch)
    make_pptx(tmp_path / "deck.pptx", {"ppt/slides/slide1.xml": slide_xml("Calibri")})

    result = CliRunner().invoke(
        app,
        ["resolve", str(tmp_path), "--format", "json", "--provider", "apt", "--jobs", "1"],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["resolutions"][0]["requested_family"] == "Calibri"


def test_cli_resolve_only_missing_hides_exact_installed(tmp_path, monkeypatch):
    patch_fontconfig(monkeypatch)
    make_pptx(
        tmp_path / "deck.pptx",
        {"ppt/slides/slide1.xml": slide_xml("Arial", "Calibri")},
    )

    result = CliRunner().invoke(
        app,
        [
            "resolve",
            str(tmp_path),
            "--format",
            "json",
            "--provider",
            "apt",
            "--only-missing",
            "--jobs",
            "1",
        ],
    )

    assert result.exit_code == 0, result.output
    families = {
        item["requested_family"]
        for item in json.loads(result.output)["resolutions"]
    }
    assert families == {"Calibri"}


def test_cli_resolve_all_fonts_includes_exact_installed(tmp_path, monkeypatch):
    patch_fontconfig(monkeypatch)
    make_pptx(
        tmp_path / "deck.pptx",
        {"ppt/slides/slide1.xml": slide_xml("Arial", "Calibri")},
    )

    result = CliRunner().invoke(
        app,
        [
            "resolve",
            str(tmp_path),
            "--format",
            "json",
            "--provider",
            "apt",
            "--all-fonts",
            "--jobs",
            "1",
        ],
    )

    assert result.exit_code == 0, result.output
    families = {
        item["requested_family"]
        for item in json.loads(result.output)["resolutions"]
    }
    assert families == {"Arial", "Calibri"}


def test_cli_explain_wingdings_marks_unsafe(monkeypatch):
    monkeypatch.setattr(
        "pptx_font_resolver.fontconfig.installed_families",
        lambda: set(),
    )
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.engine.check_font",
        lambda family: FontStatus(family, exact_installed=False),
    )

    result = CliRunner().invoke(app, ["explain", "Wingdings", "--provider", "manual"])

    assert result.exit_code == 0, result.output
    assert "Action: unsafe_symbol_font" in result.output
    assert "Risk: high" in result.output
