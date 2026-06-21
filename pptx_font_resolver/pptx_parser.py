from __future__ import annotations

import re
import zipfile
from pathlib import Path

from .models import FontOccurrence, PresentationFonts, ThemeFonts
from .theme_resolver import (
    merge_theme_fonts,
    normalize_family,
    parse_theme_fonts,
    resolve_theme_family,
)

TYPEFACE_RE = re.compile(rb"""\btypeface\s*=\s*(['"])(.*?)\1""")

RELEVANT_XML_PREFIXES = (
    "ppt/slides/",
    "ppt/slideLayouts/",
    "ppt/slideMasters/",
    "ppt/notesSlides/",
    "ppt/notesMasters/",
    "ppt/handoutMasters/",
    "ppt/charts/",
    "ppt/tables/",
    "ppt/comments/",
)


def parse_pptx(path: Path) -> PresentationFonts:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        theme_fonts = _read_theme_fonts(archive, names)
        embedded_entries = tuple(sorted(name for name in names if name.startswith("ppt/fonts/")))

        occurrences: list[FontOccurrence] = []
        raw_fonts: set[str] = set()
        resolved_fonts: set[str] = set()

        for name in names:
            if not _is_relevant_xml(name):
                continue
            data = archive.read(name)
            for raw_value in extract_typefaces(data):
                raw_fonts.add(raw_value)
                resolved = resolve_theme_family(raw_value, theme_fonts)
                if resolved is None:
                    continue
                resolved_fonts.add(resolved)
                occurrences.append(
                    FontOccurrence(
                        family=resolved,
                        raw_family=raw_value,
                        source_xml=name,
                        source_kind=_source_kind(name),
                    )
                )

    return PresentationFonts(
        path=path,
        occurrences=tuple(occurrences),
        raw_fonts=tuple(sorted(raw_fonts, key=str.casefold)),
        resolved_fonts=tuple(sorted(resolved_fonts, key=str.casefold)),
        document_type="pptx",
        theme_fonts=theme_fonts,
        embedded_font_entries=embedded_entries,
    )


def extract_typefaces(xml_bytes: bytes) -> tuple[str, ...]:
    families: list[str] = []
    for match in TYPEFACE_RE.finditer(xml_bytes):
        try:
            raw = match.group(2).decode("utf-8")
        except UnicodeDecodeError:
            raw = match.group(2).decode("utf-8", errors="replace")
        family = normalize_family(raw)
        if family is not None:
            families.append(family)
    return tuple(families)


def _read_theme_fonts(archive: zipfile.ZipFile, names: list[str]) -> ThemeFonts:
    theme_fonts = ThemeFonts()
    for name in sorted(names):
        if name.startswith("ppt/theme/") and name.endswith(".xml"):
            theme_fonts = merge_theme_fonts(theme_fonts, parse_theme_fonts(archive.read(name)))
    return theme_fonts


def _is_relevant_xml(name: str) -> bool:
    return name.endswith(".xml") and name.startswith(RELEVANT_XML_PREFIXES)


def _source_kind(name: str) -> str:
    if name.startswith("ppt/theme/"):
        return "theme"
    if name.startswith("ppt/slides/"):
        return "slide"
    if name.startswith("ppt/slideLayouts/"):
        return "slide_layout"
    if name.startswith("ppt/slideMasters/"):
        return "slide_master"
    if name.startswith("ppt/notesSlides/"):
        return "notes_slide"
    if name.startswith("ppt/notesMasters/"):
        return "notes_master"
    if name.startswith("ppt/charts/"):
        return "chart"
    if name.startswith("ppt/tables/"):
        return "table"
    if name.startswith("ppt/comments/"):
        return "comment"
    return "unknown"

