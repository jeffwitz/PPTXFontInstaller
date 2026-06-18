from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from io import StringIO
from pathlib import Path
from typing import Any

from .models import FontStatus, FontSummary, ScanResult


def scan_to_dict(scan_result: ScanResult, fonts: tuple[FontSummary, ...]) -> dict[str, Any]:
    return {
        "root": str(scan_result.root),
        "documents_scanned": len(scan_result.documents),
        "invalid_documents": [
            {"path": str(error.path), "message": error.message} for error in scan_result.errors
        ],
        "unique_fonts": len(fonts),
        "fonts": [font_summary_to_dict(font) for font in fonts],
    }


def font_summary_to_dict(font: FontSummary) -> dict[str, Any]:
    return {
        "family": font.family,
        "occurrences": font.occurrences,
        "files": [str(path) for path in font.files],
        "embedded_in": [str(path) for path in font.embedded_in],
        "status": _status_to_dict(font.status),
        "metric_fallbacks": list(font.metric_fallbacks),
        "risk_level": font.risk_level,
        "risk_reason": font.risk_reason,
        "recommendation": font.recommendation,
    }


def to_json(scan_result: ScanResult, fonts: tuple[FontSummary, ...]) -> str:
    return json.dumps(
        scan_to_dict(scan_result, fonts),
        indent=2,
        ensure_ascii=False,
        default=_json_default,
    )


def to_csv(fonts: tuple[FontSummary, ...]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "family",
            "exact_installed",
            "fontconfig_match",
            "occurrences",
            "files",
            "embedded_in",
            "metric_fallbacks",
            "risk_level",
            "risk_reason",
            "recommendation",
        ],
    )
    writer.writeheader()
    for font in fonts:
        status = font.status
        writer.writerow(
            {
                "family": font.family,
                "exact_installed": "" if status is None else str(status.exact_installed).lower(),
                "fontconfig_match": "" if status is None else status.matched_family or "",
                "occurrences": font.occurrences,
                "files": ";".join(str(path) for path in font.files),
                "embedded_in": ";".join(str(path) for path in font.embedded_in),
                "metric_fallbacks": ";".join(font.metric_fallbacks),
                "risk_level": font.risk_level,
                "risk_reason": font.risk_reason,
                "recommendation": font.recommendation,
            }
        )
    return output.getvalue()


def to_markdown(scan_result: ScanResult, fonts: tuple[FontSummary, ...]) -> str:
    lines = [
        "# PPTX font report",
        "",
        f"- PPTX analysed: {len(scan_result.documents)}",
        f"- Invalid PPTX: {len(scan_result.errors)}",
        f"- Unique fonts: {len(fonts)}",
        "",
        "| Font | Risk | Exact installed | Fontconfig match | Occurrences | "
        "Files | Recommendation |",
        "| --- | --- | --- | --- | ---: | ---: | --- |",
    ]
    for font in fonts:
        status = font.status
        exact = "" if status is None else str(status.exact_installed).lower()
        match = "" if status is None else status.matched_family or ""
        lines.append(
            f"| {font.family} | {font.risk_level} | {exact} | {match} | "
            f"{font.occurrences} | {len(font.files)} | {font.recommendation} |"
        )
    return "\n".join(lines) + "\n"


def write_report(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _status_to_dict(status: FontStatus | None) -> dict[str, Any] | None:
    if status is None:
        return None
    return asdict(status)


def _json_default(value: object) -> Any:
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
