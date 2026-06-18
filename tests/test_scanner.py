from __future__ import annotations

from conftest import make_pptx, slide_xml

from pptx_font_resolver.scanner import scan_folder


def test_invalid_pptx_is_reported_without_stopping_scan(tmp_path):
    make_pptx(tmp_path / "ok.pptx", {"ppt/slides/slide1.xml": slide_xml("Arial")})
    (tmp_path / "broken.pptx").write_text("not a zip", encoding="utf-8")

    result = scan_folder(tmp_path, jobs=1)

    assert len(result.documents) == 1
    assert len(result.errors) == 1
    assert result.errors[0].path.name == "broken.pptx"

