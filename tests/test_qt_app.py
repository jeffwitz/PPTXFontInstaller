from __future__ import annotations

from pathlib import Path

from pptx_font_resolver.models import FontStatus, FontSummary, ScanResult
from pptx_font_resolver.qt_app import (
    fallback_candidate,
    font_row,
    fontist_candidate,
    fontist_unavailable_message,
    google_fonts_candidate,
    install_prompt_text,
    install_result_summary,
    is_installable_font,
    manual_install_tooltip,
    qt_dependency_message,
    resolution_details_text,
    resolution_report_text,
    resolution_row,
    safe_system_packages,
    summary_text,
    system_package_candidate,
)
from pptx_font_resolver.resolution.models import FontCandidate, FontResolution, ResolutionReport


def test_qt_dependency_message_mentions_gui_extra():
    assert ".[gui]" in qt_dependency_message()


def test_fontist_unavailable_message_uses_fontist_output():
    message = fontist_unavailable_message(
        "Missing Sans",
        "",
        "Font not found locally nor available from Fontist.",
    )

    assert message == "Missing Sans: Font not found locally nor available from Fontist."


def test_fontist_unavailable_message_has_fallback_detail():
    assert (
        fontist_unavailable_message("Missing Sans", "", "")
        == "Missing Sans: not available through Fontist"
    )


def test_manual_install_tooltip_explains_manual_install():
    text = manual_install_tooltip("Cloud Font")

    assert "Cloud Font" in text
    assert "not installable with Fontist" in text
    assert "manually" in text


def test_install_result_summary_lists_unavailable_fonts():
    text = install_result_summary(
        ["Missing Sans: No formula for font.", "Office Cloud: not available"],
        [],
    )

    assert "Fonts not installable with Fontist:" in text
    assert "- Missing Sans: No formula for font." in text
    assert "- Office Cloud: not available" in text


def test_install_result_summary_lists_other_failures():
    text = install_result_summary([], ["Wingdings: Fontist install failed"])

    assert text == "Font install failures:\n- Wingdings: Fontist install failed"


def test_install_prompt_mentions_fontist_license_and_font_name():
    message = install_prompt_text("Wingdings")

    assert "Wingdings" in message
    assert "Fontist" in message
    assert "license" in message


def test_is_installable_font_requires_missing_exact_status():
    unknown = FontSummary(
        family="Unknown",
        occurrences=1,
        files=(),
        embedded_in=(),
        status=None,
        metric_fallbacks=(),
        risk_level="unknown",
        risk_reason="unknown",
        recommendation="check",
    )
    missing = FontSummary(
        family="Wingdings",
        occurrences=1,
        files=(),
        embedded_in=(),
        status=FontStatus("Wingdings", exact_installed=False),
        metric_fallbacks=(),
        risk_level="high",
        risk_reason="missing exact font",
        recommendation="install",
    )
    installed = FontSummary(
        family="Arial",
        occurrences=1,
        files=(),
        embedded_in=(),
        status=FontStatus("Arial", exact_installed=True),
        metric_fallbacks=(),
        risk_level="none",
        risk_reason="exact font installed",
        recommendation="none",
    )

    assert is_installable_font(unknown) is True
    assert is_installable_font(missing) is True
    assert is_installable_font(installed) is False


def test_font_row_formats_status_and_counts():
    font = FontSummary(
        family="Wingdings",
        occurrences=12,
        files=(Path("deck.pptx"),),
        embedded_in=(),
        status=FontStatus(
            requested_family="Wingdings",
            exact_installed=False,
            matched_family="Arimo",
            is_substituted=True,
        ),
        metric_fallbacks=(),
        risk_level="high",
        risk_reason="symbol font substituted",
        recommendation="install_exact_symbol_font_or_check_symbols_manually",
    )

    assert font_row(font) == [
        "Wingdings",
        "high",
        "no",
        "Arimo",
        "12",
        "1",
        "install_exact_symbol_font_or_check_symbols_manually",
    ]


def test_resolution_row_formats_cdc_columns(tmp_path):
    resolution = FontResolution(
        requested_family="Calibri",
        exact_installed=False,
        candidates=(
            FontCandidate(
                requested_family="Calibri",
                provided_family="Carlito",
                source="distro-package",
                relation="metric-compatible",
                installable=True,
                confidence=0.8,
                package_name="fonts-crosextra-carlito",
            ),
        ),
        recommended_candidate=FontCandidate(
            requested_family="Calibri",
            provided_family="Carlito",
            source="distro-package",
            relation="metric-compatible",
            installable=True,
            confidence=0.8,
            package_name="fonts-crosextra-carlito",
        ),
        recommended_action="install_metric_compatible",
        risk_level="medium",
        notes=(),
    )

    assert resolution_row(resolution, {"Calibri": (tmp_path / "deck.pptx",)}) == [
        "Calibri",
        "no",
        "no",
        "install_metric_compatible",
        "Carlito",
        "metric-compatible",
        "distro-package",
        "medium",
        "1",
    ]


def test_resolution_details_include_relation_source_and_files(tmp_path):
    resolution = FontResolution(
        requested_family="Calibri",
        exact_installed=False,
        candidates=(),
        recommended_candidate=FontCandidate(
            requested_family="Calibri",
            provided_family="Carlito",
            source="distro-package",
            relation="metric-compatible",
            installable=True,
            confidence=0.8,
            package_name="fonts-crosextra-carlito",
            install_command=("sudo", "apt", "install", "fonts-crosextra-carlito"),
        ),
        recommended_action="install_metric_compatible",
        risk_level="medium",
        notes=("metric-compatible fallback",),
    )

    text = resolution_details_text(resolution, (tmp_path / "deck.pptx",))

    assert "Recommended family: Carlito" in text
    assert "Relation: metric-compatible" in text
    assert "Source: distro-package" in text
    assert "sudo apt install fonts-crosextra-carlito" in text
    assert "deck.pptx" in text


def test_safe_system_packages_excludes_high_risk_symbol_fonts():
    safe = FontResolution(
        requested_family="Calibri",
        exact_installed=False,
        candidates=(),
        recommended_candidate=FontCandidate(
            requested_family="Calibri",
            provided_family="Carlito",
            source="distro-package",
            relation="metric-compatible",
            installable=True,
            confidence=0.8,
            package_name="fonts-crosextra-carlito",
        ),
        recommended_action="install_metric_compatible",
        risk_level="medium",
        notes=(),
    )
    unsafe = FontResolution(
        requested_family="Wingdings",
        exact_installed=False,
        candidates=(),
        recommended_candidate=FontCandidate(
            requested_family="Wingdings",
            provided_family="Wingdings",
            source="distro-package",
            relation="exact",
            installable=True,
            confidence=0.8,
            package_name="unsafe-package",
        ),
        recommended_action="unsafe_symbol_font",
        risk_level="high",
        notes=(),
    )
    report = ResolutionReport(
        scanned_files=1,
        requested_fonts=2,
        missing_fonts=2,
        resolved_exact=0,
        resolved_metric=1,
        manual_required=1,
        unsafe=1,
        resolutions=(safe, unsafe),
    )

    assert safe_system_packages(report) == ("fonts-crosextra-carlito",)
    assert "Unsafe recommendations: 1" in resolution_report_text(report)


def test_selected_resolution_action_candidates_are_safe():
    fontist = FontCandidate(
        requested_family="Calibri",
        provided_family="Calibri",
        source="fontist",
        relation="exact",
        installable=True,
        confidence=0.9,
    )
    system = FontCandidate(
        requested_family="Calibri",
        provided_family="Carlito",
        source="distro-package",
        relation="metric-compatible",
        installable=True,
        confidence=0.8,
        package_name="fonts-crosextra-carlito",
    )
    resolution = FontResolution(
        requested_family="Calibri",
        exact_installed=False,
        candidates=(fontist, system),
        recommended_candidate=system,
        recommended_action="install_metric_compatible",
        risk_level="medium",
        notes=(),
    )
    unsafe = FontResolution(
        requested_family="Wingdings",
        exact_installed=False,
        candidates=(system,),
        recommended_candidate=system,
        recommended_action="unsafe_symbol_font",
        risk_level="high",
        notes=(),
    )

    assert fontist_candidate(resolution) == fontist
    assert system_package_candidate(resolution) == system
    assert fallback_candidate(resolution) == system
    assert system_package_candidate(unsafe) is None


def test_google_fonts_candidate_requires_exact_google_source():
    google = FontCandidate(
        requested_family="Merriweather",
        provided_family="Merriweather",
        source="google-fonts",
        relation="visual-substitute",
        installable=True,
        confidence=0.86,
    )
    resolution = FontResolution(
        requested_family="Merriweather",
        exact_installed=False,
        candidates=(google,),
        recommended_candidate=google,
        recommended_action="use_visual_fallback",
        risk_level="medium",
        notes=(),
    )

    assert google_fonts_candidate(resolution) == google


def test_google_fonts_candidate_requires_installable_candidate():
    google = FontCandidate(
        requested_family="Futura PT Bold",
        provided_family="Montserrat",
        source="google-fonts",
        relation="visual-substitute",
        installable=False,
        confidence=0.86,
    )
    resolution = FontResolution(
        requested_family="Futura PT Bold",
        exact_installed=False,
        candidates=(google,),
        recommended_candidate=google,
        recommended_action="use_visual_fallback",
        risk_level="medium",
        notes=(),
    )

    assert google_fonts_candidate(resolution) is None


def test_summary_text_counts_high_risk_and_missing_fonts(tmp_path):
    scan = ScanResult(root=tmp_path, documents=(), errors=())
    font = FontSummary(
        family="Wingdings",
        occurrences=1,
        files=(),
        embedded_in=(),
        status=FontStatus("Wingdings", exact_installed=False),
        metric_fallbacks=(),
        risk_level="high",
        risk_reason="symbol font substituted",
        recommendation="install",
    )

    from pptx_font_resolver.analysis import AnalysisResult

    text = summary_text(AnalysisResult(scan=scan, fonts=(font,)))

    assert "Unique fonts: 1" in text
    assert "Missing exact fonts: 1" in text
    assert "High-risk substitutions: 1" in text



def test_install_header_toggles_visible_installable_fonts(monkeypatch):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from pptx_font_resolver.analysis import AnalysisResult
    from pptx_font_resolver.qt_app import _load_qt_modules, build_main_window

    qt = _load_qt_modules()
    Qt = qt["Qt"]
    QApplication = qt["QApplication"]
    app = QApplication.instance() or QApplication([])
    MainWindow = build_main_window(qt)
    window = MainWindow()
    missing_a = FontSummary(
        family="Wingdings",
        occurrences=1,
        files=(),
        embedded_in=(),
        status=FontStatus("Wingdings", exact_installed=False),
        metric_fallbacks=(),
        risk_level="high",
        risk_reason="missing exact font",
        recommendation="install",
    )
    missing_b = FontSummary(
        family="Symbol",
        occurrences=1,
        files=(),
        embedded_in=(),
        status=FontStatus("Symbol", exact_installed=False),
        metric_fallbacks=(),
        risk_level="high",
        risk_reason="missing exact font",
        recommendation="install",
    )
    window.analysis = AnalysisResult(
        scan=ScanResult(root=Path("."), documents=(), errors=()),
        fonts=(missing_a, missing_b),
    )
    window.populate_table()

    assert window.table.horizontalHeaderItem(0).checkState() == Qt.Unchecked

    window.toggle_all_install_checks(0)

    assert window.table.item(0, 0).checkState() == Qt.Checked
    assert window.table.item(1, 0).checkState() == Qt.Checked
    assert window.table.horizontalHeaderItem(0).checkState() == Qt.Checked

    window.table.item(0, 0).setCheckState(Qt.Unchecked)

    assert window.table.horizontalHeaderItem(0).checkState() == Qt.PartiallyChecked

    window.close()
    app.processEvents()


def test_resolution_table_displays_cdc_columns(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from pptx_font_resolver.analysis import AnalysisResult
    from pptx_font_resolver.qt_app import _load_qt_modules, build_main_window

    qt = _load_qt_modules()
    QApplication = qt["QApplication"]
    app = QApplication.instance() or QApplication([])
    MainWindow = build_main_window(qt)
    window = MainWindow()
    font = FontSummary(
        family="Calibri",
        occurrences=1,
        files=(tmp_path / "deck.pptx",),
        embedded_in=(),
        status=FontStatus("Calibri", exact_installed=False),
        metric_fallbacks=(),
        risk_level="medium",
        risk_reason="missing exact font",
        recommendation="install metric-compatible fallback",
    )
    resolution = FontResolution(
        requested_family="Calibri",
        exact_installed=False,
        candidates=(),
        recommended_candidate=FontCandidate(
            requested_family="Calibri",
            provided_family="Carlito",
            source="distro-package",
            relation="metric-compatible",
            installable=True,
            confidence=0.8,
            package_name="fonts-crosextra-carlito",
        ),
        recommended_action="install_metric_compatible",
        risk_level="medium",
        notes=(),
    )
    window.analysis = AnalysisResult(
        scan=ScanResult(root=tmp_path, documents=(), errors=()),
        fonts=(font,),
    )
    window.resolution_report = ResolutionReport(
        scanned_files=1,
        requested_fonts=1,
        missing_fonts=1,
        resolved_exact=0,
        resolved_metric=1,
        manual_required=0,
        unsafe=0,
        resolutions=(resolution,),
    )

    window.populate_resolution_table()

    assert window.table.horizontalHeaderItem(0).text() == "Family"
    assert window.table.horizontalHeaderItem(3).text() == "Recommended action"
    assert window.table.item(0, 0).text() == "Calibri"
    assert window.table.item(0, 4).text() == "Carlito"
    assert window.table.item(0, 8).text() == "1"

    window.close()
    app.processEvents()


def test_resolution_selection_enables_google_button(monkeypatch, tmp_path):
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")

    from pptx_font_resolver.analysis import AnalysisResult
    from pptx_font_resolver.qt_app import _load_qt_modules, build_main_window

    qt = _load_qt_modules()
    QApplication = qt["QApplication"]
    app = QApplication.instance() or QApplication([])
    MainWindow = build_main_window(qt)
    window = MainWindow()
    font = FontSummary(
        family="Merriweather",
        occurrences=1,
        files=(tmp_path / "deck.pptx",),
        embedded_in=(),
        status=FontStatus("Merriweather", exact_installed=False),
        metric_fallbacks=(),
        risk_level="low",
        risk_reason="missing exact font",
        recommendation="install google font",
    )
    google = FontCandidate(
        requested_family="Merriweather",
        provided_family="Merriweather",
        source="google-fonts",
        relation="exact",
        installable=True,
        confidence=0.86,
    )
    resolution = FontResolution(
        requested_family="Merriweather",
        exact_installed=False,
        candidates=(google,),
        recommended_candidate=google,
        recommended_action="install_google_font",
        risk_level="low",
        notes=(),
    )
    window.analysis = AnalysisResult(
        scan=ScanResult(root=tmp_path, documents=(), errors=()),
        fonts=(font,),
    )
    window.resolution_report = ResolutionReport(
        scanned_files=1,
        requested_fonts=1,
        missing_fonts=1,
        resolved_exact=0,
        resolved_metric=0,
        manual_required=0,
        unsafe=0,
        resolutions=(resolution,),
    )

    window.populate_resolution_table()
    window.table.selectRow(0)
    app.processEvents()

    assert window.install_google_button.isEnabled() is True
    assert window.install_system_button.isEnabled() is False

    window.close()
    app.processEvents()
