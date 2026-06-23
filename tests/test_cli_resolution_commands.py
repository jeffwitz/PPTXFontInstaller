from __future__ import annotations

import json

from conftest import make_pptx, slide_xml
from typer.testing import CliRunner

from pptx_font_resolver.cli import app
from pptx_font_resolver.resolution.fontconfig_aliases import (
    FontconfigAlias,
    FontconfigAliasResult,
)
from pptx_font_resolver.resolution.models import FontCandidate, FontResolution, ResolutionReport
from pptx_font_resolver.resolution.report import to_csv, to_json, to_markdown


def test_cli_explain_reports_metric_recommendation(monkeypatch):
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.engine.check_font",
        lambda family: None,
    )

    result = CliRunner().invoke(app, ["explain", "Calibri", "--provider", "apt"])

    assert result.exit_code == 0, result.output
    assert "Requested font: Calibri" in result.output
    assert "Action: install_metric_compatible" in result.output
    assert "Family: Carlito" in result.output


def test_cli_import_font_dry_run_prints_manual_report(tmp_path, monkeypatch):
    font = tmp_path / "Demo.ttf"
    font.write_bytes(b"fake")
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.manual_import.read_font_families",
        lambda path: ("Demo Family",),
    )

    result = CliRunner().invoke(app, ["import-font", str(font), "--dry-run"])

    assert result.exit_code == 0, result.output
    assert "Manual font import" in result.output
    assert "Demo Family" in result.output
    assert "dry-run" in result.output


def test_cli_install_missing_apt_dry_run_does_not_execute(tmp_path, monkeypatch):
    make_pptx(tmp_path / "deck.pptx", {"ppt/slides/slide1.xml": slide_xml("Calibri")})
    monkeypatch.setattr(
        "pptx_font_resolver.fontconfig.installed_families",
        lambda: set(),
    )
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.engine.check_font",
        lambda family: None,
    )
    calls = []
    monkeypatch.setattr(
        "pptx_font_resolver.cli.subprocess.run",
        lambda command, **kwargs: calls.append(command),
    )

    result = CliRunner().invoke(
        app,
        [
            "install-missing",
            str(tmp_path),
            "--provider",
            "apt",
            "--dry-run",
            "--jobs",
            "1",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "fonts-crosextra-carlito" in result.output
    assert "Aucune commande exécutée" in result.output
    assert calls == []


def test_cli_accept_fallback_writes_fontconfig_alias(tmp_path, monkeypatch):
    calls = []

    def fake_apply(requested_family, fallback_family, *, relation, source, refresh_cache):
        calls.append((requested_family, fallback_family, relation, source, refresh_cache))
        return FontconfigAliasResult(
            alias=FontconfigAlias(
                requested_family=requested_family,
                fallback_family=fallback_family,
                relation=relation,
                source=source,
            ),
            store_path=tmp_path / "aliases.json",
            config_path=tmp_path / "90-pptx-font-resolver.conf",
            cache_refreshed=refresh_cache,
        )

    monkeypatch.setattr("pptx_font_resolver.cli.apply_fontconfig_alias", fake_apply)

    result = CliRunner().invoke(
        app,
        [
            "accept-fallback",
            "Futura PT Bold",
            "Montserrat",
            "--relation",
            "visual-substitute",
            "--source",
            "google-fonts",
        ],
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        ("Futura PT Bold", "Montserrat", "visual-substitute", "google-fonts", True)
    ]
    assert "Futura PT Bold -> Montserrat" in result.output
    assert "Cache refreshed: yes" in result.output


def test_resolution_reports_include_cdc_fields():
    report = ResolutionReport(
        scanned_files=1,
        requested_fonts=1,
        missing_fonts=1,
        resolved_exact=0,
        resolved_metric=1,
        manual_required=0,
        unsafe=0,
        resolutions=(
            FontResolution(
                requested_family="Calibri",
                exact_installed=False,
                candidates=(),
                recommended_candidate=FontCandidate(
                    requested_family="Calibri",
                    provided_family="Carlito",
                    source="distro-package",
                    relation="metric-compatible",
                    installable=True,
                    confidence=0.82,
                    package_name="fonts-crosextra-carlito",
                    install_command=("sudo", "apt", "install", "fonts-crosextra-carlito"),
                    license_hint="OFL-1.1",
                ),
                recommended_action="install_metric_compatible",
                risk_level="medium",
                notes=(),
            ),
        ),
    )

    payload = json.loads(to_json(report))
    csv_report = to_csv(report)
    markdown = to_markdown(report)

    assert payload["summary"]["manual_required"] == 0
    assert payload["resolutions"][0]["recommended_action"] == "install_metric_compatible"
    assert "recommended_family" in csv_report
    assert "relation" in csv_report
    assert "sudo apt install fonts-crosextra-carlito" in csv_report
    assert "## Missing fonts resolution report" in markdown
    assert "| Calibri | install_metric_compatible | Carlito" in markdown
