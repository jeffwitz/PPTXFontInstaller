from __future__ import annotations

from conftest import document_xml, make_docx, make_pptx, slide_xml

from pptx_font_resolver.scanner import iter_document_paths, iter_pptx_paths


def test_depth_zero_scans_only_root_directory(tmp_path):
    root_file = make_pptx(tmp_path / "root.pptx", {"ppt/slides/slide1.xml": slide_xml("Arial")})
    make_pptx(tmp_path / "child" / "nested.pptx", {"ppt/slides/slide1.xml": slide_xml("Calibri")})
    (tmp_path / "ignored.txt").write_text("nope", encoding="utf-8")

    assert iter_pptx_paths(tmp_path, depth=0) == (root_file.resolve(),)


def test_depth_one_includes_direct_children(tmp_path):
    root_file = make_pptx(tmp_path / "root.pptx", {"ppt/slides/slide1.xml": slide_xml("Arial")})
    child_file = make_pptx(
        tmp_path / "child" / "nested.pptx", {"ppt/slides/slide1.xml": slide_xml("Calibri")}
    )
    make_pptx(
        tmp_path / "child" / "grandchild" / "deep.pptx",
        {"ppt/slides/slide1.xml": slide_xml("Cambria")},
    )

    assert iter_pptx_paths(tmp_path, depth=1) == (child_file.resolve(), root_file.resolve())



def test_document_path_walk_includes_pptx_and_docx(tmp_path):
    deck = make_pptx(tmp_path / "deck.pptx", {"ppt/slides/slide1.xml": slide_xml("Arial")})
    doc = make_docx(tmp_path / "brief.docx", {"word/document.xml": document_xml("Calibri")})
    (tmp_path / "ignored.xlsx").write_text("nope", encoding="utf-8")

    assert iter_document_paths(tmp_path, depth=0) == (doc.resolve(), deck.resolve())


def test_pptx_path_walk_keeps_legacy_pptx_only_behavior(tmp_path):
    deck = make_pptx(tmp_path / "deck.pptx", {"ppt/slides/slide1.xml": slide_xml("Arial")})
    make_docx(tmp_path / "brief.docx", {"word/document.xml": document_xml("Calibri")})

    assert iter_pptx_paths(tmp_path, depth=0) == (deck.resolve(),)
