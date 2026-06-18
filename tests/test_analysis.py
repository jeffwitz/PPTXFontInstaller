from __future__ import annotations

from conftest import make_pptx, slide_xml

from pptx_font_resolver.analysis import analyze_path


def test_analyze_path_returns_shared_summary(tmp_path):
    make_pptx(tmp_path / "deck.pptx", {"ppt/slides/slide1.xml": slide_xml("Calibri")})

    result = analyze_path(tmp_path, jobs=1, use_fontconfig=False)

    assert result.documents_scanned == 1
    assert result.invalid_documents == 0
    assert result.unique_fonts == 1
    assert result.missing_fonts == result.fonts
