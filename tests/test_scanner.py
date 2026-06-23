from __future__ import annotations

from conftest import document_xml, make_docx, make_pptx, slide_xml

from pptx_font_resolver.scanner import scan_folder


def test_invalid_pptx_is_reported_without_stopping_scan(tmp_path):
    make_pptx(tmp_path / "ok.pptx", {"ppt/slides/slide1.xml": slide_xml("Arial")})
    (tmp_path / "broken.pptx").write_text("not a zip", encoding="utf-8")

    result = scan_folder(tmp_path, jobs=1)

    assert len(result.documents) == 1
    assert len(result.errors) == 1
    assert result.errors[0].path.name == "broken.pptx"



def test_unreadable_directory_is_reported_without_stopping_scan(tmp_path, monkeypatch):
    make_pptx(tmp_path / "ok.pptx", {"ppt/slides/slide1.xml": slide_xml("Arial")})
    denied = tmp_path / "denied"
    denied.mkdir()
    original_iterdir = type(tmp_path).iterdir

    def fake_iterdir(self):
        if self == denied:
            raise PermissionError(13, "Permission denied", str(self))
        return original_iterdir(self)

    monkeypatch.setattr(type(tmp_path), "iterdir", fake_iterdir)

    result = scan_folder(tmp_path, jobs=1)

    assert len(result.documents) == 1
    assert any(error.path == denied for error in result.errors)


def test_scan_folder_parses_pptx_and_docx(tmp_path):
    make_pptx(tmp_path / "deck.pptx", {"ppt/slides/slide1.xml": slide_xml("Arial")})
    make_docx(tmp_path / "brief.docx", {"word/document.xml": document_xml("Calibri")})

    result = scan_folder(tmp_path, jobs=1)

    assert [document.document_type for document in result.documents] == ["docx", "pptx"]
    assert result.unique_fonts == ("Arial", "Calibri")


def test_invalid_docx_is_reported_without_stopping_scan(tmp_path):
    make_docx(tmp_path / "ok.docx", {"word/document.xml": document_xml("Calibri")})
    (tmp_path / "broken.docx").write_text("not a zip", encoding="utf-8")

    result = scan_folder(tmp_path, jobs=1)

    assert len(result.documents) == 1
    assert len(result.errors) == 1
    assert result.errors[0].path.name == "broken.docx"


def test_scan_folder_reports_oversized_xml_and_continues(tmp_path, monkeypatch):
    from pptx_font_resolver import scanner

    monkeypatch.setattr(scanner, "MAX_XML_SIZE", 10)
    make_pptx(tmp_path / "oversized.pptx", {"ppt/slides/slide1.xml": slide_xml("Calibri")})
    make_pptx(tmp_path / "valid.pptx", {"ppt/slides/slide1.xml": ""})

    result = scan_folder(tmp_path, jobs=1)

    assert len(result.documents) == 1
    assert len(result.errors) == 1
    assert "XML entry exceeds limit" in result.errors[0].message
