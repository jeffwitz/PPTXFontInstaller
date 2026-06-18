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
        summaries.append(
            FontSummary(
                family=family,
                occurrences=counts[family],
                files=tuple(sorted(files[family], key=lambda path: str(path).casefold())),
                embedded_in=tuple(sorted(embedded[family], key=lambda path: str(path).casefold())),
                status=status,
                metric_fallbacks=fallbacks,
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
    if metric_fallbacks:
        return "use_metric_compatible_fallback_or_install_exact_font"
    if status is not None and status.matched_family:
        return "review_fontconfig_substitution"
    return "unresolved"
