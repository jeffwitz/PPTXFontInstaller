from __future__ import annotations

from conftest import make_pptx, slide_xml
from typer.testing import CliRunner

from pptx_font_resolver.cli import app
from pptx_font_resolver.resolution.providers import DistroPackageProvider


def test_distro_provider_proposes_carlito_for_calibri():
    candidate = DistroPackageProvider().candidates_for("Calibri")[0]

    assert candidate.provided_family == "Carlito"
    assert candidate.package_name == "fonts-crosextra-carlito"
    assert candidate.install_command == ("sudo", "apt", "install", "fonts-crosextra-carlito")


def test_distro_provider_proposes_caladea_for_cambria():
    candidate = DistroPackageProvider().candidates_for("Cambria")[0]

    assert candidate.provided_family == "Caladea"
    assert candidate.package_name == "fonts-crosextra-caladea"
    assert candidate.relation == "metric-compatible"


def test_distro_provider_proposes_noto_cjk_package():
    candidate = DistroPackageProvider().candidates_for("Noto Sans CJK SC")[0]

    assert candidate.provided_family == "Noto Sans CJK SC"
    assert candidate.package_name == "fonts-noto-cjk"
    assert candidate.relation == "exact"


def test_install_missing_apt_dry_run_never_executes_apt(tmp_path, monkeypatch):
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
    assert calls == []
