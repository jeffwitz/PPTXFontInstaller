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

    requested_key = _casefold(font_name)
    exact = requested_key in installed
    resolved_family = font_name if exact else None
    detection_note = None

    if not exact:
        base_family = strip_style_suffix(font_name)
        if base_family != font_name and _casefold(base_family) in installed:
            exact = True
            resolved_family = base_family
            detection_note = (
                "matched installed base family after removing style suffix: "
                f"{base_family}"
            )
            matched_family, matched_file = fc_match(base_family)

    substituted = matched_family is not None and _casefold(matched_family) != requested_key
    return FontStatus(
        requested_family=font_name,
        exact_installed=exact,
        matched_family=matched_family,
        matched_file=matched_file,
        is_substituted=not exact and substituted,
        resolved_family=resolved_family,
        detection_note=detection_note,
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


def strip_style_suffix(font_name: str) -> str:
    """Remove only unambiguous style suffixes that are often not part of a family name."""
    words = font_name.split()
    while len(words) > 1 and words[-1].casefold() in {"regular"}:
        words.pop()
    return " ".join(words)
