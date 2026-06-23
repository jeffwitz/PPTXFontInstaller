from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from .analysis import AnalysisResult
from .fontist_backend import FontistBackend
from .models import FontSummary
from .report import to_csv, to_json, to_markdown, write_report
from .resolution import default_engine
from .resolution.manual_import import ManualImportError, import_font_path
from .resolution.models import FontResolution, ResolutionReport
from .resolution.report import (
    to_csv as resolution_to_csv,
)
from .resolution.report import (
    to_json as resolution_to_json,
)
from .resolution.report import (
    to_markdown as resolution_to_markdown,
)
from .resolver import build_font_report
from .scanner import default_jobs, scan_folder


def qt_dependency_message() -> str:
    return (
        "The Qt GUI requires PySide6. Install it with: "
        "python -m pip install -e \".[gui]\""
    )


def font_row(font: FontSummary) -> list[str]:
    status = font.status
    exact = "unknown" if status is None else ("yes" if status.exact_installed else "no")
    match = "" if status is None else status.matched_family or ""
    return [
        font.family,
        font.risk_level,
        exact,
        match,
        str(font.occurrences),
        str(len(font.files)),
        font.recommendation,
    ]


def resolution_row(
    resolution: FontResolution,
    files_by_family: dict[str, tuple[Path, ...]] | None = None,
) -> list[str]:
    candidate = resolution.recommended_candidate
    fontist_available = any(
        item.source == "fontist" and item.relation == "exact" for item in resolution.candidates
    )
    files = () if files_by_family is None else files_by_family.get(resolution.requested_family, ())
    return [
        resolution.requested_family,
        "yes" if resolution.exact_installed else "no",
        "yes" if fontist_available else "no",
        resolution.recommended_action,
        "" if candidate is None else candidate.provided_family,
        "" if candidate is None else candidate.relation,
        "" if candidate is None else candidate.source,
        resolution.risk_level,
        str(len(files)),
    ]


def resolution_details_text(
    resolution: FontResolution,
    files: tuple[Path, ...] = (),
) -> str:
    candidate = resolution.recommended_candidate
    lines = [
        f"Font: {resolution.requested_family}",
        f"Installed exactly: {'yes' if resolution.exact_installed else 'no'}",
        f"Recommended action: {resolution.recommended_action}",
        f"Risk: {resolution.risk_level}",
    ]
    if candidate is not None:
        lines.extend(
            [
                "",
                f"Recommended family: {candidate.provided_family}",
                f"Relation: {candidate.relation}",
                f"Source: {candidate.source}",
            ]
        )
        if candidate.package_name:
            lines.append(f"Package: {candidate.package_name}")
        if candidate.install_command:
            lines.append(f"Command: {' '.join(candidate.install_command)}")
        if candidate.license_hint:
            lines.append(f"License: {candidate.license_hint}")
        if candidate.warning:
            lines.append(f"Warning: {candidate.warning}")
    if resolution.notes:
        lines.extend(["", "Notes:"])
        lines.extend(f"- {note}" for note in resolution.notes)
    if files:
        lines.extend(["", "Files:"])
        lines.extend(f"- {path}" for path in files)
    return "\n".join(lines)


def files_by_family(fonts: tuple[FontSummary, ...]) -> dict[str, tuple[Path, ...]]:
    return {font.family: font.files for font in fonts}


def safe_system_packages(report: ResolutionReport) -> tuple[str, ...]:
    packages: set[str] = set()
    for resolution in report.resolutions:
        candidate = resolution.recommended_candidate
        if candidate is None or candidate.package_name is None:
            continue
        if candidate.source != "distro-package":
            continue
        if resolution.risk_level == "high":
            continue
        if candidate.relation not in {"exact", "metric-compatible"}:
            continue
        if resolution.recommended_action not in {
            "install_distro_package",
            "install_metric_compatible",
        }:
            continue
        packages.add(candidate.package_name)
    return tuple(sorted(packages, key=str.casefold))


def resolution_report_text(report: ResolutionReport) -> str:
    return (
        "Resolution report\n"
        f"Scanned files: {report.scanned_files}\n"
        f"Requested fonts: {report.requested_fonts}\n"
        f"Missing exact fonts: {report.missing_fonts}\n"
        f"Metric-compatible recommendations: {report.resolved_metric}\n"
        f"Manual imports required: {report.manual_required}\n"
        f"Unsafe recommendations: {report.unsafe}"
    )


def summary_text(analysis: AnalysisResult) -> str:
    high_risk = sum(1 for font in analysis.fonts if font.risk_level == "high")
    missing = len(analysis.missing_fonts)
    return (
        f"Documents analysed: {analysis.documents_scanned}\n"
        f"Invalid documents: {analysis.invalid_documents}\n"
        f"Unique fonts: {analysis.unique_fonts}\n"
        f"Missing exact fonts: {missing}\n"
        f"High-risk substitutions: {high_risk}"
    )


def install_prompt_text(font_name: str) -> str:
    return (
        f"Install {font_name} locally with Fontist and accept its license "
        "if Fontist requires one?"
    )


def is_installable_font(font: FontSummary) -> bool:
    return font.status is None or not font.status.exact_installed


def fontist_unavailable_message(font_name: str, stdout: str, stderr: str) -> str:
    detail = stderr.strip() or stdout.strip() or "not available through Fontist"
    return f"{font_name}: {detail}"


def manual_install_tooltip(font_name: str) -> str:
    return (
        f"{font_name} is not installable with Fontist. "
        "Install this font manually."
    )


def install_result_summary(unavailable: list[str], failures: list[str]) -> str:
    lines: list[str] = []
    if unavailable:
        lines.append("Fonts not installable with Fontist:")
        lines.extend(f"- {message}" for message in unavailable)
    if failures:
        if lines:
            lines.append("")
        lines.append("Font install failures:")
        lines.extend(f"- {message}" for message in failures)
    return "\n".join(lines)


def _load_qt_modules() -> dict[str, Any]:
    try:
        from PySide6 import QtCore, QtGui, QtWidgets
    except ImportError as exc:
        raise RuntimeError(qt_dependency_message()) from exc

    return {
        "Qt": QtCore.Qt,
        "QThread": QtCore.QThread,
        "Signal": QtCore.Signal,
        "QApplication": QtWidgets.QApplication,
        "QColor": QtGui.QColor,
        "QCheckBox": QtWidgets.QCheckBox,
        "QFileDialog": QtWidgets.QFileDialog,
        "QHBoxLayout": QtWidgets.QHBoxLayout,
        "QHeaderView": QtWidgets.QHeaderView,
        "QLabel": QtWidgets.QLabel,
        "QLineEdit": QtWidgets.QLineEdit,
        "QMainWindow": QtWidgets.QMainWindow,
        "QMessageBox": QtWidgets.QMessageBox,
        "QPushButton": QtWidgets.QPushButton,
        "QSpinBox": QtWidgets.QSpinBox,
        "QTableWidget": QtWidgets.QTableWidget,
        "QTableWidgetItem": QtWidgets.QTableWidgetItem,
        "QTextEdit": QtWidgets.QTextEdit,
        "QVBoxLayout": QtWidgets.QVBoxLayout,
        "QWidget": QtWidgets.QWidget,
    }


def build_main_window(qt: dict[str, Any]):
    Qt = qt["Qt"]
    QThread = qt["QThread"]
    Signal = qt["Signal"]
    QColor = qt["QColor"]
    QCheckBox = qt["QCheckBox"]
    QFileDialog = qt["QFileDialog"]
    QHBoxLayout = qt["QHBoxLayout"]
    QHeaderView = qt["QHeaderView"]
    QLabel = qt["QLabel"]
    QLineEdit = qt["QLineEdit"]
    QMainWindow = qt["QMainWindow"]
    QMessageBox = qt["QMessageBox"]
    QPushButton = qt["QPushButton"]
    QSpinBox = qt["QSpinBox"]
    QTableWidget = qt["QTableWidget"]
    QTableWidgetItem = qt["QTableWidgetItem"]
    QTextEdit = qt["QTextEdit"]
    QVBoxLayout = qt["QVBoxLayout"]
    QWidget = qt["QWidget"]

    class ScanWorker(QThread):
        finished = Signal(object)
        failed = Signal(str)
        progress = Signal(str)

        def __init__(self, folder: Path, depth: str, jobs: int) -> None:
            super().__init__()
            self.folder = folder
            self.depth = depth
            self.jobs = jobs

        def run(self) -> None:
            try:
                self.progress.emit(f"Discovering Office documents under {self.folder}...")
                scan = scan_folder(self.folder, depth=self.depth, jobs=self.jobs)
                self.progress.emit(
                    f"Analysed {len(scan.documents)} documents; checking Fontconfig..."
                )
                fonts = build_font_report(scan, use_fontconfig=True)
                self.progress.emit(f"Built font report with {len(fonts)} unique fonts.")
                self.finished.emit(AnalysisResult(scan=scan, fonts=fonts))
            except Exception as exc:
                self.failed.emit(str(exc))

    class InstallWorker(QThread):
        progress = Signal(str)
        installed = Signal(str)
        unavailable = Signal(str, str)
        failed = Signal(str, str)

        def __init__(self, font_names: list[str], location: str = "user") -> None:
            super().__init__()
            self.font_names = font_names
            self.location = location

        def run(self) -> None:
            try:
                backend = FontistBackend()
                for index, font_name in enumerate(self.font_names, start=1):
                    self.progress.emit(
                        f"Checking {font_name} in Fontist ({index}/{len(self.font_names)})..."
                    )
                    probe = backend.probe_install(font_name)
                    if not probe.available:
                        self.unavailable.emit(
                            font_name,
                            fontist_unavailable_message(
                                font_name,
                                probe.stdout,
                                probe.stderr,
                            ),
                        )
                        continue

                    self.progress.emit(
                        f"Installing {font_name} ({index}/{len(self.font_names)})..."
                    )
                    result = backend.install(
                        font_name,
                        accept_license=True,
                        location=self.location,
                        update_fontconfig=True,
                    )
                    if result.installed:
                        self.installed.emit(font_name)
                        self.progress.emit(f"Installed {font_name}.")
                    else:
                        message = result.stderr.strip() or result.stdout.strip()
                        detail = message or "Fontist install failed"
                        self.failed.emit(font_name, f"{font_name}: {detail}")
            except Exception as exc:
                self.failed.emit("Fontist", f"Unexpected install error: {exc}")

    class ResolveWorker(QThread):
        finished = Signal(object)
        failed = Signal(str)
        progress = Signal(str)

        def __init__(self, families: tuple[str, ...], scanned_files: int) -> None:
            super().__init__()
            self.families = families
            self.scanned_files = scanned_files

        def run(self) -> None:
            try:
                self.progress.emit("Resolving fonts with local, Fontist, apt, and fallback data...")
                engine = default_engine(provider="all", accept_license=False)
                report = engine.resolve_many(self.families, scanned_files=self.scanned_files)
                self.finished.emit(report)
            except Exception as exc:
                self.failed.emit(str(exc))

    class MainWindow(QMainWindow):
        font_columns = [
            "Install",
            "Font",
            "Risk",
            "Exact",
            "Fontconfig match",
            "Occurrences",
            "Files",
            "Recommendation",
        ]
        resolution_columns = [
            "Family",
            "Installed",
            "Fontist",
            "Recommended action",
            "Recommended family",
            "Relation",
            "Source",
            "Risk",
            "Files",
        ]
        columns = font_columns

        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Office Font Resolver")
            self.resize(1100, 720)
            self.analysis: AnalysisResult | None = None
            self.worker: ScanWorker | None = None
            self.install_worker: InstallWorker | None = None
            self.resolve_worker: ResolveWorker | None = None
            self.resolution_report: ResolutionReport | None = None
            self.table_mode = "fonts"
            self.updating_install_checks = False
            self.install_unavailable: list[str] = []
            self.install_failures: list[str] = []
            self.install_statuses: dict[str, str] = {}
            self.install_messages: dict[str, str] = {}
            self.pending_install_summary: str | None = None

            self.path_edit = QLineEdit()
            self.path_edit.setPlaceholderText("Folder containing PPTX or DOCX files")
            self.browse_button = QPushButton("Browse")
            self.depth_edit = QLineEdit("infinite")
            self.depth_edit.setMaximumWidth(110)
            self.jobs_spin = QSpinBox()
            self.jobs_spin.setRange(1, 64)
            self.jobs_spin.setValue(default_jobs())
            self.only_missing = QCheckBox("Only missing")
            self.scan_button = QPushButton("Scan")
            self.install_button = QPushButton("Install selected")
            self.install_all_button = QPushButton("Install all missing")
            self.resolve_button = QPushButton("Resolve all")
            self.explain_button = QPushButton("Explain")
            self.safe_install_button = QPushButton("Install safe recommendations")
            self.import_font_button = QPushButton("Import font file")
            self.export_json_button = QPushButton("Export JSON")
            self.export_csv_button = QPushButton("Export CSV")
            self.export_md_button = QPushButton("Export Markdown")

            self.summary = QTextEdit()
            self.summary.setReadOnly(True)
            self.summary.setMaximumHeight(130)
            self.table = QTableWidget(0, len(self.font_columns))
            self.table.setHorizontalHeaderLabels(self.font_columns)
            self.configure_install_header()
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.table.setSelectionBehavior(QTableWidget.SelectRows)
            self.table.setEditTriggers(QTableWidget.NoEditTriggers)
            self.details = QTextEdit()
            self.details.setReadOnly(True)
            self.details.setMaximumHeight(170)

            top = QHBoxLayout()
            top.addWidget(QLabel("Folder"))
            top.addWidget(self.path_edit, 1)
            top.addWidget(self.browse_button)
            top.addWidget(QLabel("Depth"))
            top.addWidget(self.depth_edit)
            top.addWidget(QLabel("Jobs"))
            top.addWidget(self.jobs_spin)
            top.addWidget(self.only_missing)
            top.addWidget(self.scan_button)
            top.addWidget(self.install_button)
            top.addWidget(self.install_all_button)
            top.addWidget(self.resolve_button)

            exports = QHBoxLayout()
            exports.addWidget(self.explain_button)
            exports.addWidget(self.safe_install_button)
            exports.addWidget(self.import_font_button)
            exports.addStretch(1)
            exports.addWidget(self.export_json_button)
            exports.addWidget(self.export_csv_button)
            exports.addWidget(self.export_md_button)

            layout = QVBoxLayout()
            layout.addLayout(top)
            layout.addWidget(self.summary)
            layout.addWidget(self.table, 1)
            layout.addWidget(self.details)
            layout.addLayout(exports)

            root = QWidget()
            root.setLayout(layout)
            self.setCentralWidget(root)

            self.browse_button.clicked.connect(self.choose_folder)
            self.scan_button.clicked.connect(self.start_scan)
            self.only_missing.stateChanged.connect(self.refresh_current_table)
            self.install_button.clicked.connect(self.install_selected_fonts)
            self.install_all_button.clicked.connect(self.install_all_missing_fonts)
            self.resolve_button.clicked.connect(self.resolve_all_fonts)
            self.explain_button.clicked.connect(self.explain_selected_font)
            self.safe_install_button.clicked.connect(self.install_safe_recommendations)
            self.import_font_button.clicked.connect(self.import_font_file)
            self.table.itemSelectionChanged.connect(self.show_selected_details)
            self.table.itemChanged.connect(self.sync_install_header_state)
            self.table.horizontalHeader().sectionClicked.connect(
                self.toggle_all_install_checks
            )
            self.export_json_button.clicked.connect(lambda: self.export_report("json"))
            self.export_csv_button.clicked.connect(lambda: self.export_report("csv"))
            self.export_md_button.clicked.connect(lambda: self.export_report("markdown"))
            self._set_export_enabled(False)
            self.install_button.setEnabled(False)
            self.install_all_button.setEnabled(False)
            self.resolve_button.setEnabled(False)
            self.explain_button.setEnabled(False)
            self.safe_install_button.setEnabled(False)
            self.import_font_button.setEnabled(False)

        def configure_install_header(self) -> None:
            item = QTableWidgetItem("Install")
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setToolTip("Select all visible installable fonts")
            self.table.setHorizontalHeaderItem(0, item)

        def choose_folder(self) -> None:
            folder = QFileDialog.getExistingDirectory(self, "Select folder")
            if folder:
                self.path_edit.setText(folder)

        def start_scan(self) -> None:
            folder = Path(self.path_edit.text()).expanduser()
            if not folder.exists():
                QMessageBox.warning(self, "Invalid folder", "Select an existing folder first.")
                return
            self.scan_button.setEnabled(False)
            self.summary.setPlainText("Scanning...")
            self.table.setRowCount(0)
            self.details.clear()
            self.worker = ScanWorker(
                folder,
                self.depth_edit.text().strip() or "infinite",
                self.jobs_spin.value(),
            )
            self.worker.progress.connect(self.scan_progress)
            self.worker.finished.connect(self.scan_finished)
            self.worker.failed.connect(self.scan_failed)
            self.worker.start()

        def scan_progress(self, message: str) -> None:
            self.summary.setPlainText(message)

        def scan_finished(self, analysis: AnalysisResult) -> None:
            self.analysis = analysis
            self.resolution_report = None
            self.table_mode = "fonts"
            text = summary_text(analysis)
            if self.pending_install_summary:
                text = f"{text}\n\n{self.pending_install_summary}"
                self.pending_install_summary = None
            self.summary.setPlainText(text)
            self.populate_table()
            self.scan_button.setEnabled(True)
            self.resolve_button.setEnabled(True)
            self.import_font_button.setEnabled(True)
            self._set_export_enabled(True)

        def scan_failed(self, message: str) -> None:
            self.scan_button.setEnabled(True)
            self._set_export_enabled(False)
            QMessageBox.critical(self, "Scan failed", message)

        def refresh_current_table(self) -> None:
            if self.table_mode == "resolution":
                self.populate_resolution_table()
            else:
                self.populate_table()

        def populate_table(self) -> None:
            if self.analysis is None:
                return
            self.table_mode = "fonts"
            self.table.setColumnCount(len(self.font_columns))
            self.table.setHorizontalHeaderLabels(self.font_columns)
            self.configure_install_header()
            fonts = self.displayed_fonts()
            self.updating_install_checks = True
            self.table.setRowCount(len(fonts))
            for row, font in enumerate(fonts):
                install_item = QTableWidgetItem("")
                install_item.setData(Qt.UserRole, font)
                if is_installable_font(font):
                    install_item.setFlags(
                        Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsUserCheckable
                    )
                    install_item.setCheckState(Qt.Unchecked)
                else:
                    install_item.setFlags(Qt.ItemIsSelectable)
                    install_item.setCheckState(Qt.Unchecked)
                self.table.setItem(row, 0, install_item)
                for offset, value in enumerate(font_row(font), start=1):
                    item = QTableWidgetItem(value)
                    item.setData(Qt.UserRole, font)
                    self.table.setItem(row, offset, item)
                self.apply_install_status(row, font)
            self.updating_install_checks = False
            self.table.resizeRowsToContents()
            has_installable = any(is_installable_font(font) for font in fonts)
            has_missing = bool(self.analysis.missing_fonts)
            self.install_button.setEnabled(has_installable)
            self.install_all_button.setEnabled(has_missing)
            self.explain_button.setEnabled(False)
            self.safe_install_button.setEnabled(False)
            self.sync_install_header_state()

        def resolve_all_fonts(self) -> None:
            if self.analysis is None:
                return
            self.resolve_button.setEnabled(False)
            self.scan_button.setEnabled(False)
            self.summary.setPlainText("Resolving fonts...")
            self.resolve_worker = ResolveWorker(
                self.analysis.scan.unique_fonts,
                len(self.analysis.scan.documents),
            )
            self.resolve_worker.progress.connect(self.scan_progress)
            self.resolve_worker.finished.connect(self.resolve_finished)
            self.resolve_worker.failed.connect(self.resolve_failed)
            self.resolve_worker.start()

        def resolve_finished(self, report: ResolutionReport) -> None:
            if self.resolve_worker is not None:
                self.resolve_worker.deleteLater()
                self.resolve_worker = None
            self.resolution_report = report
            self.summary.setPlainText(resolution_report_text(report))
            self.populate_resolution_table()
            self.resolve_button.setEnabled(True)
            self.scan_button.setEnabled(True)
            self.explain_button.setEnabled(True)
            self.safe_install_button.setEnabled(bool(safe_system_packages(report)))

        def resolve_failed(self, message: str) -> None:
            if self.resolve_worker is not None:
                self.resolve_worker.deleteLater()
                self.resolve_worker = None
            self.resolve_button.setEnabled(True)
            self.scan_button.setEnabled(True)
            QMessageBox.critical(self, "Resolve failed", message)

        def populate_resolution_table(self) -> None:
            if self.resolution_report is None:
                return
            self.table_mode = "resolution"
            self.table.setColumnCount(len(self.resolution_columns))
            self.table.setHorizontalHeaderLabels(self.resolution_columns)
            resolutions = self.displayed_resolutions()
            family_files = {} if self.analysis is None else files_by_family(self.analysis.fonts)
            self.updating_install_checks = True
            self.table.setRowCount(len(resolutions))
            for row, resolution in enumerate(resolutions):
                for column, value in enumerate(resolution_row(resolution, family_files)):
                    item = QTableWidgetItem(value)
                    item.setData(Qt.UserRole, resolution)
                    self.table.setItem(row, column, item)
                self.apply_resolution_status(row, resolution)
            self.updating_install_checks = False
            self.table.resizeRowsToContents()
            self.install_button.setEnabled(False)
            self.install_all_button.setEnabled(False)
            self.explain_button.setEnabled(bool(resolutions))
            self.safe_install_button.setEnabled(bool(safe_system_packages(self.resolution_report)))

        def displayed_resolutions(self) -> tuple[FontResolution, ...]:
            if self.resolution_report is None:
                return ()
            if not self.only_missing.isChecked():
                return self.resolution_report.resolutions
            return tuple(
                resolution
                for resolution in self.resolution_report.resolutions
                if not resolution.exact_installed
            )

        def toggle_all_install_checks(self, section: int) -> None:
            if self.table_mode != "fonts" or section != 0:
                return
            header_item = self.table.horizontalHeaderItem(0)
            if header_item is None:
                return
            target = (
                Qt.Unchecked
                if header_item.checkState() == Qt.Checked
                else Qt.Checked
            )
            self.updating_install_checks = True
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item is not None and item.flags() & Qt.ItemIsUserCheckable:
                    item.setCheckState(target)
            self.updating_install_checks = False
            self.sync_install_header_state()

        def sync_install_header_state(self, _item=None) -> None:
            if self.table_mode != "fonts" or self.updating_install_checks:
                return
            header_item = self.table.horizontalHeaderItem(0)
            if header_item is None:
                return
            checkable: list[QTableWidgetItem] = []
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item is not None and item.flags() & Qt.ItemIsUserCheckable:
                    checkable.append(item)
            self.updating_install_checks = True
            if not checkable:
                header_item.setCheckState(Qt.Unchecked)
            elif all(item.checkState() == Qt.Checked for item in checkable):
                header_item.setCheckState(Qt.Checked)
            elif any(item.checkState() == Qt.Checked for item in checkable):
                header_item.setCheckState(Qt.PartiallyChecked)
            else:
                header_item.setCheckState(Qt.Unchecked)
            self.updating_install_checks = False

        def displayed_fonts(self) -> tuple[FontSummary, ...]:
            if self.analysis is None:
                return ()
            if not self.only_missing.isChecked():
                return self.analysis.fonts
            missing = {font.family for font in self.analysis.missing_fonts}
            highlighted = set(self.install_statuses)
            return tuple(
                font
                for font in self.analysis.fonts
                if font.family in missing or font.family in highlighted
            )

        def apply_install_status(self, row: int, font: FontSummary) -> None:
            status = self.install_statuses.get(font.family)
            if status is None:
                return
            if status == "installed":
                color = QColor("#d9f2df")
                tooltip = self.install_messages.get(
                    font.family,
                    f"{font.family} was installed with Fontist.",
                )
            elif status == "unavailable":
                color = QColor("#f8d7da")
                tooltip = manual_install_tooltip(font.family)
            else:
                color = QColor("#fff3cd")
                tooltip = self.install_messages.get(
                    font.family,
                    f"{font.family} could not be installed with Fontist.",
                )
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                if item is not None:
                    item.setBackground(color)
                    item.setToolTip(tooltip)

        def apply_resolution_status(self, row: int, resolution: FontResolution) -> None:
            if resolution.exact_installed:
                color = QColor("#d9f2df")
                tooltip = "Exact font installed."
            elif resolution.risk_level == "high":
                color = QColor("#f8d7da")
                tooltip = "High-risk font resolution; install or review manually."
            elif resolution.recommended_candidate is not None:
                color = QColor("#fff3cd")
                tooltip = "Recommended fallback or install action available."
            else:
                color = QColor("#f8d7da")
                tooltip = "No automatic resolution available; install manually."
            for column in range(self.table.columnCount()):
                item = self.table.item(row, column)
                if item is not None:
                    item.setBackground(color)
                    item.setToolTip(tooltip)

        def show_selected_details(self) -> None:
            selected = self.table.selectedItems()
            if not selected:
                self.details.clear()
                return
            payload = selected[0].data(Qt.UserRole)
            if isinstance(payload, FontResolution):
                family_files = {} if self.analysis is None else files_by_family(self.analysis.fonts)
                self.details.setPlainText(
                    resolution_details_text(
                        payload,
                        family_files.get(payload.requested_family, ()),
                    )
                )
                return
            font = payload
            lines = [
                f"Font: {font.family}",
                f"Risk: {font.risk_level} - {font.risk_reason}",
                f"Recommendation: {font.recommendation}",
                "",
                "Files:",
            ]
            lines.extend(f"- {path}" for path in font.files)
            self.details.setPlainText("\n".join(lines))

        def explain_selected_font(self) -> None:
            selected = self.table.selectedItems()
            if not selected:
                QMessageBox.information(self, "Explain", "Select a font row first.")
                return
            payload = selected[0].data(Qt.UserRole)
            if isinstance(payload, FontResolution):
                resolution = payload
            else:
                engine = default_engine(provider="all", accept_license=False)
                resolution = engine.resolve_family(payload.family)
            family_files = {} if self.analysis is None else files_by_family(self.analysis.fonts)
            text = resolution_details_text(
                resolution,
                family_files.get(resolution.requested_family, ()),
            )
            self.details.setPlainText(text)
            QMessageBox.information(self, "Font explanation", text)

        def install_safe_recommendations(self) -> None:
            if self.resolution_report is None:
                QMessageBox.information(self, "Install recommendations", "Resolve fonts first.")
                return
            packages = safe_system_packages(self.resolution_report)
            if not packages:
                QMessageBox.information(
                    self,
                    "Install recommendations",
                    "No safe system package recommendations are available.",
                )
                return
            message = QMessageBox(self)
            message.setWindowTitle("Install system packages")
            message.setText(
                "Run sudo apt install for these recommended packages?\n\n"
                + "\n".join(packages)
            )
            yes_button = message.addButton("Yes", QMessageBox.YesRole)
            no_button = message.addButton("No", QMessageBox.NoRole)
            message.setDefaultButton(no_button)
            message.exec()
            if message.clickedButton() != yes_button:
                return
            result = subprocess.run(["sudo", "apt", "install", *packages], check=False)
            if result.returncode == 0:
                QMessageBox.information(
                    self,
                    "Install recommendations",
                    "System packages installed. Refreshing scan.",
                )
                self.start_scan()
            else:
                QMessageBox.critical(
                    self,
                    "Install recommendations failed",
                    f"apt exited with code {result.returncode}",
                )

        def import_font_file(self) -> None:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Import font file",
                "",
                "Font files (*.ttf *.otf *.ttc)",
            )
            if not path:
                return
            try:
                results = import_font_path(Path(path), recursive=False, refresh_cache=True)
            except ManualImportError as exc:
                QMessageBox.critical(self, "Import font failed", str(exc))
                return
            imported = "\n".join(
                f"{result.target_path}: {', '.join(result.family_names)}" for result in results
            )
            QMessageBox.information(self, "Font imported", imported)
            if self.analysis is not None:
                self.start_scan()

        def selected_install_fonts(self) -> list[FontSummary]:
            selected: list[FontSummary] = []
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 0)
                if item is None or item.checkState() != Qt.Checked:
                    continue
                font = item.data(Qt.UserRole)
                if is_installable_font(font):
                    selected.append(font)
            return selected

        def install_selected_fonts(self) -> None:
            selected = self.selected_install_fonts()
            if not selected:
                QMessageBox.information(
                    self,
                    "No fonts selected",
                    "Check one or more missing fonts first.",
                )
                return

            accepted: list[str] = []
            accept_all = False
            for font in selected:
                if not accept_all:
                    answer = self.ask_install_decision(font.family)
                    if answer == "no":
                        continue
                    if answer == "all":
                        accept_all = True
                accepted.append(font.family)

            if accepted:
                self.start_font_install(
                    accepted,
                    f"Installing {len(accepted)} selected font(s)...",
                )

        def install_all_missing_fonts(self) -> None:
            if self.analysis is None:
                return
            fonts = [font for font in self.analysis.missing_fonts if is_installable_font(font)]
            if not fonts:
                QMessageBox.information(
                    self,
                    "No missing fonts",
                    "No missing exact fonts were found.",
                )
                return
            if not self.ask_install_all_decision(len(fonts)):
                return
            self.start_font_install(
                [font.family for font in fonts],
                f"Installing {len(fonts)} missing font(s)...",
            )

        def start_font_install(self, font_names: list[str], message: str) -> None:
            self.install_unavailable = []
            self.install_failures = []
            self.pending_install_summary = None
            for font_name in font_names:
                self.install_statuses.pop(font_name, None)
                self.install_messages.pop(font_name, None)
            self.install_button.setEnabled(False)
            self.install_all_button.setEnabled(False)
            self.scan_button.setEnabled(False)
            self.summary.setPlainText(message)
            self.install_worker = InstallWorker(font_names, location="user")
            self.install_worker.progress.connect(self.scan_progress)
            self.install_worker.installed.connect(self.install_succeeded)
            self.install_worker.unavailable.connect(self.install_unavailable_font)
            self.install_worker.failed.connect(self.install_failed)
            self.install_worker.finished.connect(self.install_finished)
            self.install_worker.start()

        def ask_install_decision(self, font_name: str) -> str:
            message = QMessageBox(self)
            message.setWindowTitle("Install font")
            message.setText(install_prompt_text(font_name))
            yes_button = message.addButton("Yes", QMessageBox.YesRole)
            all_button = message.addButton("All", QMessageBox.AcceptRole)
            no_button = message.addButton("No", QMessageBox.NoRole)
            message.setDefaultButton(yes_button)
            message.exec()
            clicked = message.clickedButton()
            if clicked == no_button:
                return "no"
            if clicked == all_button:
                return "all"
            return "yes"

        def ask_install_all_decision(self, count: int) -> bool:
            message = QMessageBox(self)
            message.setWindowTitle("Install missing fonts")
            message.setText(
                f"Try to install all {count} missing font(s) with Fontist and "
                "accept licenses if Fontist requires them?"
            )
            yes_button = message.addButton("Yes", QMessageBox.YesRole)
            no_button = message.addButton("No", QMessageBox.NoRole)
            message.setDefaultButton(yes_button)
            message.exec()
            return message.clickedButton() != no_button

        def install_succeeded(self, font_name: str) -> None:
            self.install_statuses[font_name] = "installed"
            self.install_messages[font_name] = f"{font_name} was installed with Fontist."

        def install_unavailable_font(self, font_name: str, message: str) -> None:
            self.install_unavailable.append(message)
            self.install_statuses[font_name] = "unavailable"
            self.install_messages[font_name] = manual_install_tooltip(font_name)
            self.summary.append(f"Not installable with Fontist: {message}")

        def install_failed(self, font_name: str, message: str) -> None:
            self.install_failures.append(message)
            self.install_statuses[font_name] = "failed"
            self.install_messages[font_name] = message
            self.summary.append(f"Install failed: {message}")

        def install_finished(self) -> None:
            if self.install_worker is not None:
                self.install_worker.deleteLater()
                self.install_worker = None
            self.pending_install_summary = install_result_summary(
                self.install_unavailable,
                self.install_failures,
            )
            self.summary.append("Installation finished. Refreshing scan...")
            self.scan_button.setEnabled(True)
            self.start_scan()

        def closeEvent(self, event) -> None:
            running = [
                worker
                for worker in (self.worker, self.install_worker, self.resolve_worker)
                if worker is not None and worker.isRunning()
            ]
            if running:
                QMessageBox.information(
                    self,
                    "Operation running",
                    "Wait for the current scan or install to finish before closing.",
                )
                event.ignore()
                return
            super().closeEvent(event)

        def export_report(self, format_name: str) -> None:
            if self.analysis is None:
                return
            suffix = {"json": "json", "csv": "csv", "markdown": "md"}[format_name]
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Export report",
                f"pptx-font-report.{suffix}",
                f"*.{suffix}",
            )
            if not path:
                return
            output = Path(path)
            if self.table_mode == "resolution" and self.resolution_report is not None:
                if format_name == "json":
                    content = resolution_to_json(self.resolution_report)
                elif format_name == "csv":
                    content = resolution_to_csv(self.resolution_report)
                else:
                    content = resolution_to_markdown(self.resolution_report)
            else:
                if format_name == "json":
                    content = to_json(self.analysis.scan, self.analysis.fonts)
                elif format_name == "csv":
                    content = to_csv(self.analysis.fonts)
                else:
                    content = to_markdown(self.analysis.scan, self.analysis.fonts)
            write_report(output, content)

        def _set_export_enabled(self, enabled: bool) -> None:
            self.export_json_button.setEnabled(enabled)
            self.export_csv_button.setEnabled(enabled)
            self.export_md_button.setEnabled(enabled)

    return MainWindow


def main() -> None:
    try:
        qt = _load_qt_modules()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc

    QApplication = qt["QApplication"]
    MainWindow = build_main_window(qt)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.raise_()
    window.activateWindow()
    raise SystemExit(app.exec())


if __name__ == "__main__":
    main()
