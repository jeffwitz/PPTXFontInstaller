from __future__ import annotations

from conftest import document_theme_xml, document_xml, make_docx, theme_xml

from pptx_font_resolver.docx_parser import extract_docx_fonts, parse_docx
from pptx_font_resolver.models import ThemeFonts


def test_extract_docx_fonts_from_rfonts_attributes():
    xml = document_xml("Calibri", "Yu Gothic").encode()

    assert extract_docx_fonts(xml) == ("Calibri", "Yu Gothic")


def test_extract_docx_fonts_resolves_word_theme_attributes():
    xml = document_theme_xml("minorHAnsi").encode()
    theme = ThemeFonts(minor_latin="Aptos")

    assert extract_docx_fonts(xml, theme) == ("Aptos",)


def test_parse_docx_reads_document_styles_headers_and_theme(tmp_path):
    path = make_docx(
        tmp_path / "brief.docx",
        {
            "word/theme/theme1.xml": theme_xml(minor_latin="Aptos"),
            "word/document.xml": document_theme_xml("minorHAnsi"),
            "word/styles.xml": document_xml("Times New Roman"),
            "word/header1.xml": document_xml("Arial"),
        },
    )

    parsed = parse_docx(path)

    assert parsed.document_type == "docx"
    assert parsed.theme_fonts.minor_latin == "Aptos"
    assert parsed.resolved_fonts == ("Aptos", "Arial", "Times New Roman")
    assert {occurrence.source_kind for occurrence in parsed.occurrences} == {
        "document",
        "style",
        "header",
    }


def test_parse_docx_detects_embedded_font_entries(tmp_path):
    path = make_docx(
        tmp_path / "brief.docx",
        {
            "word/document.xml": document_xml("Aptos"),
            "word/fonts/font1.odttf": b"fake-font",
        },
    )

    parsed = parse_docx(path)

    assert parsed.embedded_font_entries == ("word/fonts/font1.odttf",)
