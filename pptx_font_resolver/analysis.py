from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .models import FontSummary, ScanResult
from .resolver import build_font_report
from .scanner import scan_folder


@dataclass(frozen=True)
class AnalysisResult:
    scan: ScanResult
    fonts: tuple[FontSummary, ...]

    @property
    def documents_scanned(self) -> int:
        return len(self.scan.documents)

    @property
    def invalid_documents(self) -> int:
        return len(self.scan.errors)

    @property
    def unique_fonts(self) -> int:
        return len(self.fonts)

    @property
    def missing_fonts(self) -> tuple[FontSummary, ...]:
        return tuple(
            font for font in self.fonts if font.status is None or not font.status.exact_installed
        )


def analyze_path(
    path: Path,
    *,
    depth: int | str | None = "infinite",
    jobs: int | None = None,
    use_fontconfig: bool = True,
) -> AnalysisResult:
    scan = scan_folder(path, depth=depth, jobs=jobs)
    fonts = build_font_report(scan, use_fontconfig=use_fontconfig)
    return AnalysisResult(scan=scan, fonts=fonts)
