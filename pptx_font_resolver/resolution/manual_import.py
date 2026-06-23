from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pptx_font_resolver.fontconfig import clear_fontconfig_cache

SUPPORTED_FONT_SUFFIXES = frozenset({".ttf", ".otf", ".ttc"})


class ManualImportError(RuntimeError):
    """Raised when a user-supplied font file cannot be imported."""


@dataclass(frozen=True)
class ManualFontImportResult:
    source_path: Path
    target_path: Path
    family_names: tuple[str, ...]
    copied: bool
    linked: bool
    cache_refreshed: bool


def default_import_target() -> Path:
    return Path.home() / ".local" / "share" / "fonts" / "pptx-font-installer"


def iter_font_files(path: Path, *, recursive: bool = True) -> tuple[Path, ...]:
    source = path.expanduser()
    if source.is_file():
        return (source,) if _is_supported_font_file(source) else ()
    if not source.is_dir():
        raise ManualImportError(f"Font path does not exist: {path}")
    iterator = source.rglob("*") if recursive else source.iterdir()
    return tuple(
        sorted(
            (candidate for candidate in iterator if _is_supported_font_file(candidate)),
            key=lambda candidate: str(candidate).casefold(),
        )
    )


def read_font_families(path: Path) -> tuple[str, ...]:
    source = path.expanduser()
    if not _is_supported_font_file(source):
        raise ManualImportError(
            f"Unsupported font extension for {source.name}; expected .ttf, .otf, or .ttc"
        )

    try:
        from fontTools.ttLib import TTCollection, TTFont
    except ImportError as exc:
        raise ManualImportError(
            "fontTools is required to read font family names; install with "
            "`python -m pip install -e '.[font-import]'`."
        ) from exc

    try:
        fonts = TTCollection(source).fonts if source.suffix.lower() == ".ttc" else [TTFont(source)]
    except Exception as exc:
        raise ManualImportError(f"Unable to read font metadata from {source}: {exc}") from exc

    families: list[str] = []
    for font in fonts:
        families.extend(_family_names_from_font(font))
        close = getattr(font, "close", None)
        if callable(close):
            close()

    unique = tuple(dict.fromkeys(name for name in families if name))
    if not unique:
        raise ManualImportError(f"No family name found in {source}")
    return unique


def import_font_file(
    path: Path,
    *,
    target: Path | None = None,
    refresh_cache: bool = True,
    copy: bool = True,
) -> ManualFontImportResult:
    source = path.expanduser().resolve()
    if not source.is_file():
        raise ManualImportError(f"Font file does not exist: {path}")
    if not _is_supported_font_file(source):
        raise ManualImportError(
            f"Unsupported font extension for {source.name}; expected .ttf, .otf, or .ttc"
        )

    families = read_font_families(source)
    target_dir = (target or default_import_target()).expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    destination = target_dir / source.name
    linked = False
    copied = False
    if copy:
        if not destination.exists() or source != destination.resolve():
            shutil.copy2(source, destination)
        copied = True
    else:
        if destination.exists() or destination.is_symlink():
            destination.unlink()
        destination.symlink_to(source)
        linked = True

    cache_refreshed = refresh_font_cache(target_dir) if refresh_cache else False
    return ManualFontImportResult(
        source_path=source,
        target_path=destination,
        family_names=families,
        copied=copied,
        linked=linked,
        cache_refreshed=cache_refreshed,
    )


def import_font_path(
    path: Path,
    *,
    target: Path | None = None,
    recursive: bool = True,
    dry_run: bool = False,
    copy: bool = True,
    refresh_cache: bool = True,
) -> tuple[ManualFontImportResult, ...]:
    files = iter_font_files(path, recursive=recursive)
    if not files:
        raise ManualImportError(f"No .ttf, .otf, or .ttc font files found in {path}")
    if dry_run:
        return tuple(
            ManualFontImportResult(
                source_path=file.expanduser().resolve(),
                target_path=(target or default_import_target()).expanduser() / file.name,
                family_names=read_font_families(file),
                copied=False,
                linked=False,
                cache_refreshed=False,
            )
            for file in files
        )
    return tuple(
        import_font_file(file, target=target, refresh_cache=refresh_cache, copy=copy)
        for file in files
    )


def refresh_font_cache(target: Path) -> bool:
    result = subprocess.run(
        ["fc-cache", "-f", str(target.expanduser())],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "fc-cache failed"
        raise ManualImportError(detail)
    clear_fontconfig_cache()
    return True


def _is_supported_font_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in SUPPORTED_FONT_SUFFIXES


def _family_names_from_font(font: Any) -> list[str]:
    names = font["name"].names
    preferred = _decode_name_records(names, name_id=16)
    return preferred or _decode_name_records(names, name_id=1)


def _decode_name_records(records: Any, *, name_id: int) -> list[str]:
    decoded: list[str] = []
    for record in records:
        if record.nameID != name_id:
            continue
        try:
            value = record.toUnicode().strip()
        except Exception:
            continue
        if value and value not in decoded:
            decoded.append(value)
    return decoded
