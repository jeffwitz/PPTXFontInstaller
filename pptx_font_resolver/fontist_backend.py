from __future__ import annotations

import subprocess
from dataclasses import dataclass

from .fontconfig import check_font
from .models import FontStatus


@dataclass(frozen=True)
class FontistProbeResult:
    font_name: str
    available: bool
    installed: bool
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
    post_install_status: FontStatus | None = None


def output_mentions_license(text: str) -> bool:
    folded = text.casefold()
    return "license" in folded and (
        "accept" in folded or "agreement" in folded or "eula" in folded
    )


class FontistBackend:
    def probe_install(self, font_name: str, *, timeout: float = 2.0) -> FontistProbeResult:
        try:
            result = subprocess.run(
                ["fontist", "list", font_name],
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            return FontistProbeResult(
                font_name=font_name,
                available=False,
                installed=False,
                license_required=False,
                stdout="",
                stderr=f"fontist command not found: {exc.filename}",
                returncode=127,
            )
        except subprocess.TimeoutExpired:
            return FontistProbeResult(
                font_name=font_name,
                available=False,
                installed=False,
                license_required=False,
                stdout="",
                stderr=f"fontist list timed out after {timeout:g}s",
                returncode=124,
            )
        combined = f"{result.stdout}\n{result.stderr}".casefold()
        unavailable = (
            "not found locally nor available" in combined
            or "no formula" in combined
            or "not available" in combined
        )
        installed = "(installed)" in combined
        return FontistProbeResult(
            font_name=font_name,
            available=not unavailable,
            installed=installed,
            license_required=False,
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )

    def install(
        self,
        font_name: str,
        *,
        accept_license: bool,
        location: str = "user",
        update_fontconfig: bool = True,
    ) -> FontistInstallResult:
        command = ["fontist", "install", "--newest", "--location", location]
        if update_fontconfig:
            command.append("--update-fontconfig")
        if accept_license:
            command.append("--accept-all-licenses")
        command.append(font_name)
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
        except FileNotFoundError as exc:
            return FontistInstallResult(
                font_name=font_name,
                installed=False,
                stdout="",
                stderr=f"fontist command not found: {exc.filename}",
                returncode=127,
            )
        if result.returncode == 0 and update_fontconfig:
            try:
                subprocess.run(["fc-cache", "-f"], capture_output=True, text=True, check=False)
            except FileNotFoundError:
                pass
        post_status = check_font(font_name) if result.returncode == 0 else None
        return FontistInstallResult(
            font_name=font_name,
            installed=result.returncode == 0,
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
            post_install_status=post_status,
        )
