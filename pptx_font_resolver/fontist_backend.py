from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class FontistProbeResult:
    font_name: str
    available: bool
    license_required: bool
    stdout: str
    stderr: str
    returncode: int


@dataclass(frozen=True)
class FontistInstallResult:
    font_name: str
    installed: bool
    stdout: str
    stderr: str
    returncode: int


class FontistBackend:
    def probe_install(self, font_name: str) -> FontistProbeResult:
        result = subprocess.run(
            ["fontist", "install", "--newest", font_name],
            capture_output=True,
            text=True,
            check=False,
        )
        combined = f"{result.stdout}\n{result.stderr}".casefold()
        license_required = "license" in combined and (
            "accept" in combined or "agreement" in combined or "eula" in combined
        )
        available = result.returncode == 0 or license_required
        return FontistProbeResult(
            font_name=font_name,
            available=available,
            license_required=license_required,
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )

    def install(self, font_name: str, *, accept_license: bool) -> FontistInstallResult:
        command = ["fontist", "install", "--newest"]
        if accept_license:
            command.append("--accept-all-licenses")
        command.append(font_name)
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return FontistInstallResult(
            font_name=font_name,
            installed=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )

