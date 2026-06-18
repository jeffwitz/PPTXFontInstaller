from __future__ import annotations

import inspect

from pptx_font_resolver.cli import (
    _install_choice,
    _install_confirm_message,
    _install_single_font,
    install_font,
    install_missing,
)
from pptx_font_resolver.fontist_backend import FontistInstallResult, FontistProbeResult


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



def test_install_commands_accept_license_by_default():
    assert inspect.signature(install_font).parameters["accept_license"].default is True
    assert inspect.signature(install_missing).parameters["accept_license"].default is True


def test_install_confirm_message_mentions_license_acceptance():
    message = _install_confirm_message("Wingdings", accept_license=True)

    assert "Wingdings" in message
    assert "accepter sa licence" in message


def test_install_choice_supports_all(monkeypatch):
    monkeypatch.setattr("pptx_font_resolver.cli.Prompt.ask", lambda *args, **kwargs: "a")

    assert _install_choice("Wingdings", accept_license=True) == "a"
