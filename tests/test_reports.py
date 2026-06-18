from __future__ import annotations

import csv
import json
from io import StringIO

from conftest import make_pptx, slide_xml

from pptx_font_resolver.report import to_csv, to_json
from pptx_font_resolver.resolver import build_font_report
from pptx_font_resolver.scanner import scan_folder


def test_json_report_is_frontend_consumable(tmp_path):
    make_pptx(tmp_path / "deck.pptx", {"ppt/slides/slide1.xml": slide_xml("Calibri")})
    scan = scan_folder(tmp_path, jobs=1)
    fonts = build_font_report(scan, use_fontconfig=False)

    payload = json.loads(to_json(scan, fonts))

    assert payload["documents_scanned"] == 1
    assert payload["fonts"][0]["family"] == "Calibri"
    assert payload["fonts"][0]["metric_fallbacks"] == ["Carlito"]
    assert payload["fonts"][0]["risk_level"] == "medium"


def test_csv_report_is_valid(tmp_path):
    make_pptx(tmp_path / "deck.pptx", {"ppt/slides/slide1.xml": slide_xml("Arial")})
    scan = scan_folder(tmp_path, jobs=1)
    fonts = build_font_report(scan, use_fontconfig=False)

    rows = list(csv.DictReader(StringIO(to_csv(fonts))))

    assert rows[0]["family"] == "Arial"
    assert rows[0]["occurrences"] == "1"
    assert rows[0]["risk_level"] == "medium"
