from __future__ import annotations

from conftest import make_pptx, slide_xml

from pptx_font_resolver.scanner import iter_pptx_paths


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

