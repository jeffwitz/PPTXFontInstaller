from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from pptx_font_resolver.fontconfig import check_font
from pptx_font_resolver.resolver import is_symbol_font

from .data import normalize_family
from .models import FontCandidate, FontResolution, RecommendedAction, ResolutionReport
from .providers import (
    CuratedFallbackProvider,
    DistroPackageProvider,
    FontconfigFallbackProvider,
    FontistProvider,
    FontProvider,
    GoogleFontsProvider,
    LocalFontProvider,
    ManualImportProvider,
)


@dataclass
class FontResolutionEngine:
    providers: tuple[FontProvider, ...]

    def resolve_family(self, family: str) -> FontResolution:
        normalized = " ".join(family.split())
        notes: list[str] = []
        candidates: list[FontCandidate] = []
        try:
            status = check_font(normalized)
        except Exception as exc:
            status = None
            notes.append(f"Fontconfig check failed: {exc}")
        exact_installed = bool(status and status.exact_installed)

        seen: set[tuple[str, str, str]] = set()
        for provider in self.providers:
            for candidate in provider.candidates_for(normalized):
                key = (
                    normalize_family(candidate.provided_family),
                    candidate.source,
                    candidate.relation,
                )
                if key in seen:
                    continue
                seen.add(key)
                candidates.append(candidate)

        if is_symbol_font(normalized) and not exact_installed:
            notes.append("Symbol font: automatic substitution may alter glyph semantics.")
            recommended = _first_source(candidates, "manual")
            return FontResolution(
                requested_family=normalized,
                exact_installed=False,
                candidates=tuple(candidates),
                recommended_candidate=recommended,
                recommended_action="unsafe_symbol_font",
                risk_level="high",
                notes=tuple(notes),
            )

        recommended = _recommend_candidate(candidates, exact_installed)
        action = _recommended_action(recommended, exact_installed)
        risk = _risk_level(recommended, exact_installed)
        if recommended is not None and recommended.warning:
            notes.append(recommended.warning)
        if recommended is None and not exact_installed:
            notes.append("No safe automatic source found; manual review required.")
        return FontResolution(
            requested_family=normalized,
            exact_installed=exact_installed,
            candidates=tuple(candidates),
            recommended_candidate=recommended,
            recommended_action=action,
            risk_level=risk,
            notes=tuple(dict.fromkeys(notes)),
        )

    def resolve_many(
        self,
        families: Iterable[str],
        *,
        scanned_files: int = 0,
    ) -> ResolutionReport:
        unique = tuple(
            sorted(
                {" ".join(f.split()) for f in families if f.strip()},
                key=str.casefold,
            )
        )
        resolutions = tuple(self.resolve_family(family) for family in unique)
        missing = tuple(resolution for resolution in resolutions if not resolution.exact_installed)
        return ResolutionReport(
            scanned_files=scanned_files,
            requested_fonts=len(resolutions),
            missing_fonts=len(missing),
            resolved_exact=sum(1 for r in resolutions if r.exact_installed),
            resolved_metric=sum(
                1
                for r in resolutions
                if r.recommended_candidate is not None
                and r.recommended_candidate.relation == "metric-compatible"
            ),
            manual_required=sum(
                1
                for r in resolutions
                if r.recommended_action in {"manual_import", "unsafe_symbol_font"}
            ),
            unsafe=sum(1 for r in resolutions if r.risk_level == "high"),
            resolutions=resolutions,
        )


def default_engine(
    *,
    provider: str = "all",
    distro: str = "debian",
    accept_license: bool = False,
    include_fontist: bool = True,
) -> FontResolutionEngine:
    providers: list[FontProvider] = [LocalFontProvider()]
    if include_fontist and provider in {"fontist", "all"}:
        providers.append(FontistProvider(accept_license=accept_license))
    if provider in {"apt", "all"}:
        providers.append(DistroPackageProvider(distro=distro))
    if provider in {"google", "all"}:
        providers.append(GoogleFontsProvider())
    if provider == "google":
        providers.append(CuratedFallbackProvider(allowed_sources=frozenset({"google-fonts"})))
    if provider in {"manual", "all"}:
        providers.append(CuratedFallbackProvider())
        providers.append(FontconfigFallbackProvider())
        providers.append(ManualImportProvider())
    return FontResolutionEngine(tuple(providers))


def _recommend_candidate(
    candidates: list[FontCandidate],
    exact_installed: bool,
) -> FontCandidate | None:
    if exact_installed:
        return _first_relation(candidates, "exact", source="local")
    priority = {
        ("fontist", "exact"): 0,
        ("distro-package", "exact"): 1,
        ("google-fonts", "exact"): 2,
        ("distro-package", "metric-compatible"): 3,
        ("curated", "metric-compatible"): 4,
        ("google-fonts", "visual-substitute"): 5,
        ("manual", "exact"): 6,
        ("curated", "visual-substitute"): 7,
        ("fontconfig", "generic"): 8,
    }
    return min(
        candidates,
        key=lambda candidate: (
            priority.get((candidate.source, candidate.relation), 99),
            -candidate.confidence,
            candidate.provided_family.casefold(),
        ),
        default=None,
    )


def _recommended_action(
    candidate: FontCandidate | None,
    exact_installed: bool,
) -> RecommendedAction:
    if exact_installed:
        return "none"
    if candidate is None:
        return "unresolved"
    if candidate.source == "fontist" and candidate.relation == "exact":
        return "install_fontist"
    if candidate.source == "distro-package" and candidate.relation == "exact":
        return "install_distro_package"
    if candidate.source == "google-fonts" and candidate.relation == "exact":
        return "install_google_font"
    if candidate.relation == "metric-compatible":
        return "install_metric_compatible"
    if candidate.source == "manual":
        return "manual_import"
    if candidate.relation == "visual-substitute":
        return "use_visual_fallback"
    return "unresolved"


def _risk_level(candidate: FontCandidate | None, exact_installed: bool) -> str:
    if exact_installed:
        return "none"
    if candidate is None:
        return "unknown"
    if candidate.relation == "exact":
        return "low" if candidate.source != "manual" else "medium"
    if candidate.relation == "metric-compatible":
        return "medium"
    if candidate.relation == "visual-substitute":
        return "medium"
    if candidate.relation == "unsafe":
        return "high"
    return "unknown"


def _first_source(candidates: list[FontCandidate], source: str) -> FontCandidate | None:
    return next((candidate for candidate in candidates if candidate.source == source), None)


def _first_relation(
    candidates: list[FontCandidate],
    relation: str,
    *,
    source: str | None = None,
) -> FontCandidate | None:
    return next(
        (
            candidate
            for candidate in candidates
            if candidate.relation == relation and (source is None or candidate.source == source)
        ),
        None,
    )
