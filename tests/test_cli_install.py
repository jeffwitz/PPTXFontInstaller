from __future__ import annotations

import inspect

from pptx_font_resolver.cli import (
    _filter_font_summaries,
    _fontist_unavailable_detail,
    _google_install_families,
    _install_choice,
    _install_confirm_message,
    _install_single_font,
    _print_install_attempt_report,
    install_font,
    install_missing,
)
from pptx_font_resolver.fontist_backend import FontistInstallResult, FontistProbeResult
from pptx_font_resolver.models import FontStatus, FontSummary


class LicenseBackend:
    def probe_install(self, font_name: str) -> FontistProbeResult:
        return FontistProbeResult(
            font_name=font_name,
            available=True,
            installed=False,
            license_required=False,
            stdout="",
            stderr="",
            returncode=0,
        )

    def install(self, font_name: str, **kwargs) -> FontistInstallResult:
        return FontistInstallResult(
            font_name=font_name,
            installed=False,
            stdout='FONT LICENSE ACCEPTANCE REQUIRED FOR "Wingdings"',
            stderr="Fontist will not download these fonts unless you accept the terms.",
            returncode=1,
        )


def test_install_single_font_can_return_false_for_group_install(monkeypatch):
    monkeypatch.setattr("typer.confirm", lambda message: False)

    installed = _install_single_font(
        LicenseBackend(),
        "Wingdings",
        accept_license=False,
        ask_license=True,
        location="user",
        dry_run=False,
        raise_on_error=False,
    )

    assert installed is False



def test_install_commands_do_not_accept_license_by_default():
    assert inspect.signature(install_font).parameters["accept_license"].default is False
    assert inspect.signature(install_missing).parameters["accept_license"].default is False


def test_install_missing_has_all_option_disabled_by_default():
    assert inspect.signature(install_missing).parameters["all_missing"].default is False


def test_install_confirm_message_mentions_license_acceptance():
    message = _install_confirm_message("Wingdings", accept_license=True)

    assert "Wingdings" in message
    assert "accepter sa licence" in message


def test_install_choice_supports_all(monkeypatch):
    monkeypatch.setattr("pptx_font_resolver.cli.Prompt.ask", lambda *args, **kwargs: "a")

    assert _install_choice("Wingdings", accept_license=True) == "a"


def test_fontist_unavailable_detail_prefers_stderr():
    assert _fontist_unavailable_detail("stdout detail", "stderr detail") == "stderr detail"


def test_install_attempt_report_renders_statuses():
    from pptx_font_resolver import cli

    cli.console.begin_capture()
    _print_install_attempt_report([
        ("Aptos", "installée", "Fontist OK"),
        ("Cloud Font", "non installable", "install manually"),
    ])
    output = cli.console.end_capture()

    assert "Rapport installation Fontist" in output
    assert "Aptos" in output
    assert "Cloud Font" in output


def test_filter_font_summaries_defaults_to_problematic_fonts():
    installed_clean = FontSummary(
        family="Arial",
        occurrences=1,
        files=(),
        embedded_in=(),
        status=FontStatus("Arial", exact_installed=True),
        metric_fallbacks=(),
        risk_level="none",
        risk_reason="exact family installed",
        recommendation="nothing_to_do",
    )
    installed_low = FontSummary(
        family="Noto Sans CJK SC Regular",
        occurrences=1,
        files=(),
        embedded_in=(),
        status=FontStatus("Noto Sans CJK SC Regular", exact_installed=True),
        metric_fallbacks=(),
        risk_level="low",
        risk_reason="style suffix matched",
        recommendation="nothing_to_do",
    )
    missing = FontSummary(
        family="Calibri",
        occurrences=1,
        files=(),
        embedded_in=(),
        status=FontStatus("Calibri", exact_installed=False),
        metric_fallbacks=("Carlito",),
        risk_level="medium",
        risk_reason="metric fallback exists",
        recommendation="use_metric_compatible_fallback_or_install_exact_font",
    )

    assert _filter_font_summaries(
        (installed_clean, installed_low, missing),
        only_missing=False,
        all_fonts=False,
    ) == (installed_low, missing)
    assert _filter_font_summaries(
        (installed_clean, installed_low, missing),
        only_missing=True,
        all_fonts=True,
    ) == (missing,)
    assert _filter_font_summaries(
        (installed_clean, installed_low, missing),
        only_missing=False,
        all_fonts=True,
    ) == (installed_clean, installed_low, missing)


def test_google_install_families_uses_recommended_family_from_command():
    rows = [
        (
            "Futura PT Bold",
            "google-fonts",
            "",
            ("pptx-font-resolver", "install-google-font", "Montserrat"),
        ),
        (
            "Futura PT Demi",
            "google-fonts",
            "",
            ("pptx-font-resolver", "install-google-font", "Montserrat"),
        ),
        ("LegacySans-Bold", "google-fonts", "", None),
    ]

    assert _google_install_families(rows) == ("LegacySans-Bold", "Montserrat")
