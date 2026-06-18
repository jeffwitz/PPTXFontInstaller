from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from .fontconfig import check_font
from .models import FontStatus, FontSummary, ScanResult

METRIC_COMPATIBLE = {
    "Calibri": ("Carlito",),
    "Cambria": ("Caladea",),
    "Arial": ("Arial", "Liberation Sans", "Arimo"),
    "Times New Roman": ("Times New Roman", "Liberation Serif", "Tinos"),
    "Courier New": ("Courier New", "Liberation Mono", "Cousine"),
}

SYMBOL_FONTS = {
    "marlett",
    "mt extra",
    "symbol",
    "webdings",
    "wingdings",
    "wingdings 2",
    "wingdings 3",
}

DESIGN_FONT_MARKERS = (
    "futura",
    "merriweather",
    "montserrat",
    "gulliver",
    "legacy",
)

LATIN_SUBSTITUTES = {
    "arial",
    "arimo",
    "dejavu sans",
    "liberation sans",
    "noto sans",
}


def build_font_report(
    scan_result: ScanResult,
    *,
    use_fontconfig: bool = True,
) -> tuple[FontSummary, ...]:
    counts: Counter[str] = Counter()
    files: dict[str, set[Path]] = defaultdict(set)
    embedded: dict[str, set[Path]] = defaultdict(set)

    for document in scan_result.documents:
        embedded_document = bool(document.embedded_font_entries)
        for occurrence in document.occurrences:
            counts[occurrence.family] += 1
            files[occurrence.family].add(document.path)
            if embedded_document:
                embedded[occurrence.family].add(document.path)

    summaries: list[FontSummary] = []
    for family in sorted(counts, key=str.casefold):
        status = check_font(family) if use_fontconfig else None
        fallbacks = METRIC_COMPATIBLE.get(family, ())
        risk_level, risk_reason = classify_risk(
            family,
            status,
            bool(embedded[family]),
            fallbacks,
        )
        summaries.append(
            FontSummary(
                family=family,
                occurrences=counts[family],
                files=tuple(sorted(files[family], key=lambda path: str(path).casefold())),
                embedded_in=tuple(sorted(embedded[family], key=lambda path: str(path).casefold())),
                status=status,
                metric_fallbacks=fallbacks,
                risk_level=risk_level,
                risk_reason=risk_reason,
                recommendation=recommend_action(status, bool(embedded[family]), fallbacks),
            )
        )
    return tuple(summaries)


def recommend_action(
    status: FontStatus | None,
    has_embedded_font: bool,
    metric_fallbacks: tuple[str, ...],
) -> str:
    if status is not None and status.exact_installed:
        return "nothing_to_do"
    if has_embedded_font:
        return "embedded_font_present"
    if is_symbol_font(status.requested_family if status else ""):
        return "install_exact_symbol_font_or_check_symbols_manually"
    if status is not None and is_cjk_family(status.requested_family) and _is_latin_match(status):
        return "install_cjk_font_or_select_cjk_compatible_substitute"
    if metric_fallbacks:
        return "use_metric_compatible_fallback_or_install_exact_font"
    if status is not None and status.matched_family:
        return "review_fontconfig_substitution"
    return "unresolved"


def classify_risk(
    family: str,
    status: FontStatus | None,
    has_embedded_font: bool,
    metric_fallbacks: tuple[str, ...],
) -> tuple[str, str]:
    if status is not None and status.exact_installed:
        if status.detection_note:
            return "low", status.detection_note
        return "none", "exact family installed"
    if has_embedded_font:
        return "medium", "font is embedded in at least one PPTX but not installed locally"
    if is_symbol_font(family):
        return "high", "symbol font substituted; icons or bullets may render incorrectly"
    if status is not None and is_cjk_family(family) and _is_latin_match(status):
        return "high", "CJK font substituted by a Latin family"
    if metric_fallbacks:
        return "medium", "metric-compatible fallback exists but layout is not guaranteed identical"
    if _is_design_font(family):
        return "medium", "brand or design font substituted; visual differences are likely"
    if status is not None and status.is_substituted:
        return "medium", "Fontconfig substituted the requested family"
    if status is not None and status.check_error:
        return "unknown", status.check_error
    return "unknown", "font is unresolved"


def is_symbol_font(family: str) -> bool:
    return family.casefold() in SYMBOL_FONTS


def is_cjk_family(family: str) -> bool:
    cjk_keywords = ("cjk", "dengxian", "gothic", "ming", "song", "hei", "kaiti")
    folded = family.casefold()
    return any(keyword in folded for keyword in cjk_keywords) or any(
        "\u4e00" <= char <= "\u9fff" for char in family
    )


def _is_latin_match(status: FontStatus) -> bool:
    if not status.matched_family:
        return False
    return status.matched_family.casefold() in LATIN_SUBSTITUTES


def _is_design_font(family: str) -> bool:
    folded = family.casefold()
    return any(marker in folded for marker in DESIGN_FONT_MARKERS)
