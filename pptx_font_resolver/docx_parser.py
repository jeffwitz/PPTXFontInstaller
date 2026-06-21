from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree

from .models import FontOccurrence, PresentationFonts, ThemeFonts
from .pptx_parser import extract_typefaces
from .theme_resolver import merge_theme_fonts, normalize_family, parse_theme_fonts

WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

WORD_FONT_ATTRS = {"ascii", "hAnsi", "eastAsia", "cs"}
WORD_THEME_ATTRS = {"asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme", "csTheme"}

WORD_THEME_FIELDS = {
    "majorHAnsi": "major_latin",
    "minorHAnsi": "minor_latin",
    "majorAscii": "major_latin",
    "minorAscii": "minor_latin",
    "majorEastAsia": "major_ea",
    "minorEastAsia": "minor_ea",
    "majorBidi": "major_cs",
    "minorBidi": "minor_cs",
}

RELEVANT_WORD_XML = (
    "word/document.xml",
    "word/styles.xml",
    "word/numbering.xml",
    "word/settings.xml",
    "word/fontTable.xml",
    "word/footnotes.xml",
    "word/endnotes.xml",
    "word/comments.xml",
    "word/glossary/document.xml",
)

RELEVANT_WORD_PREFIXES = (
    "word/header",
    "word/footer",
    "word/charts/",
    "word/drawings/",
)


def parse_docx(path: Path) -> PresentationFonts:
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        theme_fonts = _read_theme_fonts(archive, names)
        embedded_entries = tuple(sorted(name for name in names if name.startswith("word/fonts/")))

        occurrences: list[FontOccurrence] = []
        raw_fonts: set[str] = set()
        resolved_fonts: set[str] = set()

        for name in names:
            if not _is_relevant_xml(name):
                continue
            data = archive.read(name)
            for raw_value in extract_docx_fonts(data, theme_fonts):
                raw_fonts.add(raw_value)
                resolved_fonts.add(raw_value)
                occurrences.append(
                    FontOccurrence(
                        family=raw_value,
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
        document_type="docx",
        theme_fonts=theme_fonts,
        embedded_font_entries=embedded_entries,
    )


def extract_docx_fonts(xml_bytes: bytes, theme_fonts: ThemeFonts | None = None) -> tuple[str, ...]:
    theme_fonts = theme_fonts or ThemeFonts()
    families: list[str] = []
    try:
        root = ElementTree.fromstring(xml_bytes)
    except ElementTree.ParseError:
        return extract_typefaces(xml_bytes)

    for element in root.iter():
        if _local_name(element.tag) != "rFonts":
            continue
        seen_in_element: set[str] = set()
        for attr_name, attr_value in element.attrib.items():
            local = _local_name(attr_name)
            family = _font_attr_family(local, attr_value, theme_fonts)
            if family is None or family in seen_in_element:
                continue
            seen_in_element.add(family)
            families.append(family)

    families.extend(extract_typefaces(xml_bytes))
    return tuple(families)


def _font_attr_family(attr_name: str, value: str, theme_fonts: ThemeFonts) -> str | None:
    if attr_name in WORD_FONT_ATTRS:
        return normalize_family(value)
    if attr_name in WORD_THEME_ATTRS:
        return _resolve_word_theme(value, theme_fonts)
    return None


def _resolve_word_theme(value: str, theme_fonts: ThemeFonts) -> str | None:
    field = WORD_THEME_FIELDS.get(value)
    if field is None:
        return None
    return getattr(theme_fonts, field)


def _read_theme_fonts(archive: zipfile.ZipFile, names: list[str]) -> ThemeFonts:
    theme_fonts = ThemeFonts()
    for name in sorted(names):
        if name.startswith("word/theme/") and name.endswith(".xml"):
            theme_fonts = merge_theme_fonts(theme_fonts, parse_theme_fonts(archive.read(name)))
    return theme_fonts


def _is_relevant_xml(name: str) -> bool:
    return name.endswith(".xml") and (
        name in RELEVANT_WORD_XML or name.startswith(RELEVANT_WORD_PREFIXES)
    )


def _source_kind(name: str) -> str:
    if name == "word/document.xml":
        return "document"
    if name == "word/styles.xml":
        return "style"
    if name == "word/numbering.xml":
        return "numbering"
    if name.startswith("word/header"):
        return "header"
    if name.startswith("word/footer"):
        return "footer"
    if name == "word/footnotes.xml":
        return "footnote"
    if name == "word/endnotes.xml":
        return "endnote"
    if name == "word/comments.xml":
        return "comment"
    if name.startswith("word/charts/"):
        return "chart"
    if name.startswith("word/drawings/"):
        return "drawing"
    if name.startswith("word/glossary/"):
        return "glossary"
    return "unknown"


def _local_name(name: str) -> str:
    if "}" in name:
        return name.rsplit("}", 1)[1]
    return name
