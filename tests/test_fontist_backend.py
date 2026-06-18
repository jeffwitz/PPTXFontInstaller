from __future__ import annotations

from pptx_font_resolver.fontist_backend import FontistBackend, output_mentions_license


class Completed:
    def __init__(self, args, returncode=0, stdout="", stderr=""):
        self.args = args
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_probe_never_accepts_all_licenses(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return Completed(args, returncode=1, stderr="License agreement must be accepted")

    monkeypatch.setattr("subprocess.run", fake_run)

    result = FontistBackend().probe_install("Aptos")

    assert result.available is True
    assert result.license_required is False
    assert "--accept-all-licenses" not in calls[0]
    assert calls[0][:2] == ["fontist", "list"]


def test_install_adds_license_acceptance_only_when_explicit(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return Completed(args)

    monkeypatch.setattr("subprocess.run", fake_run)

    FontistBackend().install("Aptos", accept_license=False)
    FontistBackend().install("Aptos", accept_license=True)

    install_calls = [call for call in calls if call[:2] == ["fontist", "install"]]
    assert "--accept-all-licenses" not in install_calls[0]
    assert "--accept-all-licenses" in install_calls[1]
    assert "--location" in install_calls[0]
    assert "user" in install_calls[0]


def test_output_mentions_license_detects_acceptance_prompt():
    assert output_mentions_license("License agreement must be accepted") is True
    assert output_mentions_license("Font not found") is False
