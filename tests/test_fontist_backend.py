from __future__ import annotations

from pptx_font_resolver.fontist_backend import FontistBackend


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

    assert result.license_required is True
    assert "--accept-all-licenses" not in calls[0]


def test_install_adds_license_acceptance_only_when_explicit(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        return Completed(args)

    monkeypatch.setattr("subprocess.run", fake_run)

    FontistBackend().install("Aptos", accept_license=False)
    FontistBackend().install("Aptos", accept_license=True)

    assert "--accept-all-licenses" not in calls[0]
    assert "--accept-all-licenses" in calls[1]

