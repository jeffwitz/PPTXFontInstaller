from __future__ import annotations

import subprocess

from .models import FontStatus


def check_font(font_name: str) -> FontStatus:
    try:
        installed = installed_families()
        matched_family, matched_file = fc_match(font_name)
    except FileNotFoundError as exc:
        return FontStatus(
            requested_family=font_name,
            exact_installed=False,
            check_error=f"fontconfig command not found: {exc.filename}",
        )
    except subprocess.SubprocessError as exc:
        return FontStatus(
            requested_family=font_name,
            exact_installed=False,
            check_error=str(exc),
        )

    exact = _casefold(font_name) in installed
    substituted = matched_family is not None and _casefold(matched_family) != _casefold(font_name)
    return FontStatus(
        requested_family=font_name,
        exact_installed=exact,
        matched_family=matched_family,
        matched_file=matched_file,
        is_substituted=not exact and substituted,
    )


def installed_families() -> set[str]:
    result = subprocess.run(
        ["fc-list", ":", "family"],
        check=True,
        capture_output=True,
        text=True,
    )
    families: set[str] = set()
    for line in result.stdout.splitlines():
        for family in line.split(","):
            normalized = family.strip()
            if normalized:
                families.add(_casefold(normalized))
    return families


def fc_match(font_name: str) -> tuple[str | None, str | None]:
    result = subprocess.run(
        ["fc-match", "-f", "%{family}\n%{file}\n", font_name],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = result.stdout.splitlines()
    family = lines[0].split(",", maxsplit=1)[0].strip() if lines else None
    file_path = lines[1].strip() if len(lines) > 1 and lines[1].strip() else None
    return family or None, file_path


def _casefold(value: str) -> str:
    return " ".join(value.split()).casefold()

