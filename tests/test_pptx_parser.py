from __future__ import annotations

from conftest import make_pptx, slide_xml, theme_xml

from pptx_font_resolver.pptx_parser import extract_typefaces, parse_pptx


def test_extract_typeface_from_minimal_xml():
    xml = b'<a:latin typeface="Calibri"/><a:ea typeface="Yu Gothic"/>'

    assert extract_typefaces(xml) == ("Calibri", "Yu Gothic")


def test_parse_pptx_resolves_theme_placeholders(tmp_path):
    path = make_pptx(
        tmp_path / "deck.pptx",
        {
            "ppt/theme/theme1.xml": theme_xml(minor_latin="Aptos"),
            "ppt/slides/slide1.xml": slide_xml("+mn-lt", "Arial"),
        },
    )

    parsed = parse_pptx(path)

    assert parsed.raw_fonts == ("+mn-lt", "Arial")
    assert parsed.theme_fonts.minor_latin == "Aptos"
    assert parsed.resolved_fonts == ("Aptos", "Arial")


def test_parse_pptx_detects_embedded_font_entries(tmp_path):
    path = make_pptx(
        tmp_path / "deck.pptx",
        {
            "ppt/slides/slide1.xml": slide_xml("Aptos"),
            "ppt/fonts/font1.odttf": b"fake-font",
        },
    )

    parsed = parse_pptx(path)

    assert parsed.embedded_font_entries == ("ppt/fonts/font1.odttf",)

