from __future__ import annotations

import json

from conftest import make_pptx, slide_xml
from typer.testing import CliRunner

from pptx_font_resolver.cli import app
from pptx_font_resolver.fontist_backend import FontistProbeResult
from pptx_font_resolver.resolution import FontResolutionEngine
from pptx_font_resolver.resolution.models import FontCandidate
from pptx_font_resolver.resolution.providers import (
    DistroPackageProvider,
    FontistProvider,
)


class FakeFontistBackend:
    def probe_install(self, font_name: str) -> FontistProbeResult:
        return FontistProbeResult(
            font_name=font_name,
            available=True,
            installed=False,
            license_required=True,
            stdout="",
            stderr="",
            returncode=0,
        )


class EmptyProvider:
    name = "empty"

    def candidates_for(self, family: str):
        return ()


class MetricProvider:
    name = "metric"

    def candidates_for(self, family: str):
        if family != "Calibri":
            return ()
        return (
            FontCandidate(
                requested_family=family,
                provided_family="Carlito",
                source="distro-package",
                relation="metric-compatible",
                installable=True,
                confidence=0.9,
                package_name="fonts-crosextra-carlito",
                install_command=("sudo", "apt", "install", "fonts-crosextra-carlito"),
            ),
        )


def test_fontist_provider_does_not_accept_licenses_by_default():
    provider = FontistProvider(backend=FakeFontistBackend())

    candidate = provider.candidates_for("Wingdings")[0]

    assert candidate.source == "fontist"
    assert candidate.relation == "exact"
    assert candidate.install_command is not None
    assert "--accept-all-licenses" not in candidate.install_command


def test_fontist_provider_can_emit_explicit_license_acceptance_command():
    provider = FontistProvider(backend=FakeFontistBackend(), accept_license=True)

    candidate = provider.candidates_for("Wingdings")[0]

    assert candidate.install_command is not None
    assert "--accept-all-licenses" in candidate.install_command


def test_distro_provider_proposes_metric_package_for_calibri():
    provider = DistroPackageProvider()

    candidates = provider.candidates_for("Calibri")

    assert candidates[0].provided_family == "Carlito"
    assert candidates[0].relation == "metric-compatible"
    assert candidates[0].package_name == "fonts-crosextra-carlito"


def test_resolution_engine_marks_symbol_fonts_unsafe(monkeypatch):
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.engine.check_font",
        lambda family: None,
    )
    engine = FontResolutionEngine((EmptyProvider(),))

    resolution = engine.resolve_family("Wingdings")

    assert resolution.recommended_action == "unsafe_symbol_font"
    assert resolution.risk_level == "high"
    assert "Symbol font" in resolution.notes[0]


def test_resolution_engine_recommends_metric_compatible_candidate(monkeypatch):
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.engine.check_font",
        lambda family: None,
    )
    engine = FontResolutionEngine((MetricProvider(),))

    report = engine.resolve_many(["Calibri"], scanned_files=2)

    resolution = report.resolutions[0]
    assert report.scanned_files == 2
    assert resolution.recommended_action == "install_metric_compatible"
    assert resolution.recommended_candidate is not None
    assert resolution.recommended_candidate.provided_family == "Carlito"


def test_cli_resolve_json_reports_metric_package(tmp_path, monkeypatch):
    make_pptx(tmp_path / "deck.pptx", {"ppt/slides/slide1.xml": slide_xml("Calibri")})
    monkeypatch.setattr(
        "pptx_font_resolver.fontconfig.installed_families",
        lambda: set(),
    )
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.engine.check_font",
        lambda family: None,
    )

    result = CliRunner().invoke(
        app,
        [
            "resolve",
            str(tmp_path),
            "--provider",
            "apt",
            "--format",
            "json",
            "--jobs",
            "1",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    resolution = payload["resolutions"][0]
    assert resolution["requested_family"] == "Calibri"
    assert resolution["recommended_action"] == "install_metric_compatible"
    assert resolution["recommended_candidate"]["package_name"] == "fonts-crosextra-carlito"
