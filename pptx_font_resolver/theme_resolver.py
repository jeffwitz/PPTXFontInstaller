from __future__ import annotations

from html import unescape
from xml.etree import ElementTree

from .models import ThemeFonts

THEME_PLACEHOLDERS = {
    "+mn-lt": "minor_latin",
    "+mj-lt": "major_latin",
    "+mn-ea": "minor_ea",
    "+mj-ea": "major_ea",
    "+mn-cs": "minor_cs",
    "+mj-cs": "major_cs",
}

OOXML_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def normalize_family(value: str) -> str | None:
    family = " ".join(unescape(value).strip().split())
    if not family:
        return None
    return family


def is_theme_placeholder(family: str) -> bool:
    return family in THEME_PLACEHOLDERS


def resolve_theme_family(raw_family: str, theme_fonts: ThemeFonts) -> str | None:
    field = THEME_PLACEHOLDERS.get(raw_family)
    if field is None:
        return raw_family
    return getattr(theme_fonts, field)


def parse_theme_fonts(xml_bytes: bytes) -> ThemeFonts:
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError:
        return ThemeFonts()

    major = root.find(f".//{OOXML_NS}majorFont")
    minor = root.find(f".//{OOXML_NS}minorFont")
    return ThemeFonts(
        major_latin=_typeface(major, "latin"),
        major_ea=_typeface(major, "ea"),
        major_cs=_typeface(major, "cs"),
        minor_latin=_typeface(minor, "latin"),
        minor_ea=_typeface(minor, "ea"),
        minor_cs=_typeface(minor, "cs"),
    )


def merge_theme_fonts(base: ThemeFonts, update: ThemeFonts) -> ThemeFonts:
    values = {}
    for key, value in base.as_dict().items():
        values[key] = value or getattr(update, key)
    return ThemeFonts(**values)


def _typeface(parent: ElementTree.Element | None, tag: str) -> str | None:
    if parent is None:
        return None
    element = parent.find(f"{OOXML_NS}{tag}")
    if element is None:
        return None
    value = element.attrib.get("typeface")
    return normalize_family(value) if value is not None else None

