from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RelationKind = Literal[
    "exact",
    "metric-compatible",
    "visual-substitute",
    "generic",
    "unsafe",
]

SourceKind = Literal[
    "local",
    "fontist",
    "distro-package",
    "google-fonts",
    "manual",
    "curated",
    "fontconfig",
]

RecommendedAction = Literal[
    "none",
    "install_fontist",
    "install_distro_package",
    "install_google_font",
    "install_metric_compatible",
    "manual_import",
    "use_visual_fallback",
    "unsafe_symbol_font",
    "unresolved",
]


@dataclass(frozen=True)
class FontCandidate:
    requested_family: str
    provided_family: str
    source: SourceKind
    relation: RelationKind
    installable: bool
    confidence: float
    install_command: tuple[str, ...] | None = None
    package_name: str | None = None
    license_hint: str | None = None
    url: str | None = None
    warning: str | None = None


@dataclass(frozen=True)
class FontResolution:
    requested_family: str
    exact_installed: bool
    candidates: tuple[FontCandidate, ...]
    recommended_candidate: FontCandidate | None
    recommended_action: RecommendedAction
    risk_level: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class ResolutionReport:
    scanned_files: int
    requested_fonts: int
    missing_fonts: int
    resolved_exact: int
    resolved_metric: int
    manual_required: int
    unsafe: int
    resolutions: tuple[FontResolution, ...]
