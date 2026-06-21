from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class FontOccurrence:
    family: str
    raw_family: str
    source_xml: str
    source_kind: str


@dataclass(frozen=True)
class ThemeFonts:
    minor_latin: str | None = None
    major_latin: str | None = None
    minor_ea: str | None = None
    major_ea: str | None = None
    minor_cs: str | None = None
    major_cs: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "minor_latin": self.minor_latin,
            "major_latin": self.major_latin,
            "minor_ea": self.minor_ea,
            "major_ea": self.major_ea,
            "minor_cs": self.minor_cs,
            "major_cs": self.major_cs,
        }


@dataclass(frozen=True)
class PresentationFonts:
    path: Path
    occurrences: tuple[FontOccurrence, ...]
    raw_fonts: tuple[str, ...]
    resolved_fonts: tuple[str, ...]
    document_type: str = "pptx"
    theme_fonts: ThemeFonts = field(default_factory=ThemeFonts)
    embedded_font_entries: tuple[str, ...] = ()


@dataclass(frozen=True)
class ScanError:
    path: Path
    message: str


@dataclass(frozen=True)
class ScanResult:
    root: Path
    documents: tuple[PresentationFonts, ...]
    errors: tuple[ScanError, ...] = ()

    @property
    def unique_fonts(self) -> tuple[str, ...]:
        fonts = {font for document in self.documents for font in document.resolved_fonts}
        return tuple(sorted(fonts, key=str.casefold))


@dataclass(frozen=True)
class FontStatus:
    requested_family: str
    exact_installed: bool
    matched_family: str | None = None
    matched_file: str | None = None
    is_substituted: bool = False
    resolved_family: str | None = None
    detection_note: str | None = None
    check_error: str | None = None


@dataclass(frozen=True)
class FontSummary:
    family: str
    occurrences: int
    files: tuple[Path, ...]
    embedded_in: tuple[Path, ...]
    status: FontStatus | None
    metric_fallbacks: tuple[str, ...]
    risk_level: str
    risk_reason: str
    recommendation: str
