from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from .analysis import AnalysisResult
from .models import FontSummary
from .report import to_csv, to_json, to_markdown, write_report
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


def summary_text(analysis: AnalysisResult) -> str:
    high_risk = sum(1 for font in analysis.fonts if font.risk_level == "high")
    missing = len(analysis.missing_fonts)
    return (
        f"PPTX analysed: {analysis.documents_scanned}\n"
        f"Invalid PPTX: {analysis.invalid_documents}\n"
        f"Unique fonts: {analysis.unique_fonts}\n"
        f"Missing exact fonts: {missing}\n"
        f"High-risk substitutions: {high_risk}"
    )


def _load_qt_modules() -> dict[str, Any]:
    try:
        from PySide6 import QtCore, QtWidgets
    except ImportError as exc:
        raise RuntimeError(qt_dependency_message()) from exc

    return {
        "Qt": QtCore.Qt,
        "QThread": QtCore.QThread,
        "Signal": QtCore.Signal,
        "QApplication": QtWidgets.QApplication,
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
                self.progress.emit(f"Discovering PPTX files under {self.folder}...")
                scan = scan_folder(self.folder, depth=self.depth, jobs=self.jobs)
                self.progress.emit(
                    f"Analysed {len(scan.documents)} PPTX; checking Fontconfig..."
                )
                fonts = build_font_report(scan, use_fontconfig=True)
                self.progress.emit(f"Built font report with {len(fonts)} unique fonts.")
                self.finished.emit(AnalysisResult(scan=scan, fonts=fonts))
            except Exception as exc:
                self.failed.emit(str(exc))

    class MainWindow(QMainWindow):
        columns = [
            "Font",
            "Risk",
            "Exact",
            "Fontconfig match",
            "Occurrences",
            "Files",
            "Recommendation",
        ]

        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("PPTX Font Resolver")
            self.resize(1100, 720)
            self.analysis: AnalysisResult | None = None
            self.worker: ScanWorker | None = None

            self.path_edit = QLineEdit()
            self.path_edit.setPlaceholderText("Folder containing PPTX files")
            self.browse_button = QPushButton("Browse")
            self.depth_edit = QLineEdit("infinite")
            self.depth_edit.setMaximumWidth(110)
            self.jobs_spin = QSpinBox()
            self.jobs_spin.setRange(1, 64)
            self.jobs_spin.setValue(default_jobs())
            self.only_missing = QCheckBox("Only missing")
            self.scan_button = QPushButton("Scan")
            self.export_json_button = QPushButton("Export JSON")
            self.export_csv_button = QPushButton("Export CSV")
            self.export_md_button = QPushButton("Export Markdown")

            self.summary = QTextEdit()
            self.summary.setReadOnly(True)
            self.summary.setMaximumHeight(130)
            self.table = QTableWidget(0, len(self.columns))
            self.table.setHorizontalHeaderLabels(self.columns)
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

            exports = QHBoxLayout()
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
            self.only_missing.stateChanged.connect(self.populate_table)
            self.table.itemSelectionChanged.connect(self.show_selected_details)
            self.export_json_button.clicked.connect(lambda: self.export_report("json"))
            self.export_csv_button.clicked.connect(lambda: self.export_report("csv"))
            self.export_md_button.clicked.connect(lambda: self.export_report("markdown"))
            self._set_export_enabled(False)

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
            self.summary.setPlainText(summary_text(analysis))
            self.populate_table()
            self.scan_button.setEnabled(True)
            self._set_export_enabled(True)

        def scan_failed(self, message: str) -> None:
            self.scan_button.setEnabled(True)
            self._set_export_enabled(False)
            QMessageBox.critical(self, "Scan failed", message)

        def populate_table(self) -> None:
            if self.analysis is None:
                return
            if self.only_missing.isChecked():
                fonts = self.analysis.missing_fonts
            else:
                fonts = self.analysis.fonts
            self.table.setRowCount(len(fonts))
            for row, font in enumerate(fonts):
                for column, value in enumerate(font_row(font)):
                    item = QTableWidgetItem(value)
                    item.setData(Qt.UserRole, font)
                    self.table.setItem(row, column, item)
            self.table.resizeRowsToContents()

        def show_selected_details(self) -> None:
            selected = self.table.selectedItems()
            if not selected:
                self.details.clear()
                return
            font = selected[0].data(Qt.UserRole)
            lines = [
                f"Font: {font.family}",
                f"Risk: {font.risk_level} - {font.risk_reason}",
                f"Recommendation: {font.recommendation}",
                "",
                "Files:",
            ]
            lines.extend(f"- {path}" for path in font.files)
            self.details.setPlainText("\n".join(lines))

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
