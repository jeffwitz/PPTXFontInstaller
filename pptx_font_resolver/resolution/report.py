from __future__ import annotations

import csv
import json
from dataclasses import asdict
from io import StringIO
from typing import Any

from rich.console import Console
from rich.table import Table

from .models import FontResolution, ResolutionReport


def resolution_report_to_dict(report: ResolutionReport) -> dict[str, Any]:
    summary = {
        "scanned_files": report.scanned_files,
        "requested_fonts": report.requested_fonts,
        "missing_fonts": report.missing_fonts,
        "manual_required": report.manual_required,
        "unsafe": report.unsafe,
        "resolved_exact": report.resolved_exact,
        "resolved_metric": report.resolved_metric,
    }
    return {
        "summary": summary,
        "scanned_files": report.scanned_files,
        "requested_fonts": report.requested_fonts,
        "missing_fonts": report.missing_fonts,
        "resolved_exact": report.resolved_exact,
        "resolved_metric": report.resolved_metric,
        "manual_required": report.manual_required,
        "unsafe": report.unsafe,
        "resolutions": [resolution_to_dict(resolution) for resolution in report.resolutions],
    }


def resolution_to_dict(resolution: FontResolution) -> dict[str, Any]:
    return {
        "requested_family": resolution.requested_family,
        "exact_installed": resolution.exact_installed,
        "recommended_action": resolution.recommended_action,
        "risk_level": resolution.risk_level,
        "recommended_candidate": _candidate_to_dict(resolution.recommended_candidate),
        "notes": list(resolution.notes),
        "candidates": [_candidate_to_dict(candidate) for candidate in resolution.candidates],
    }


def to_json(report: ResolutionReport) -> str:
    return json.dumps(resolution_report_to_dict(report), indent=2, ensure_ascii=False)


def to_csv(report: ResolutionReport) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "requested_family",
            "status",
            "risk_level",
            "recommended_action",
            "recommended_family",
            "relation",
            "source",
            "package_name",
            "install_command",
            "license_hint",
            "warning",
            "files",
        ],
    )
    writer.writeheader()
    for resolution in report.resolutions:
        candidate = resolution.recommended_candidate
        writer.writerow(
            {
                "requested_family": resolution.requested_family,
                "status": "installed" if resolution.exact_installed else "missing",
                "risk_level": resolution.risk_level,
                "recommended_action": resolution.recommended_action,
                "recommended_family": "" if candidate is None else candidate.provided_family,
                "relation": "" if candidate is None else candidate.relation,
                "source": "" if candidate is None else candidate.source,
                "package_name": "" if candidate is None else candidate.package_name or "",
                "install_command": ""
                if candidate is None or candidate.install_command is None
                else " ".join(candidate.install_command),
                "license_hint": "" if candidate is None else candidate.license_hint or "",
                "warning": ";".join(
                    item
                    for item in (
                        "" if candidate is None else candidate.warning or "",
                        *resolution.notes,
                    )
                    if item
                ),
                "files": "",
            }
        )
    return output.getvalue()


def to_markdown(report: ResolutionReport) -> str:
    lines = [
        "## Missing fonts resolution report",
        "",
        f"- Scanned files: {report.scanned_files}",
        f"- Requested fonts: {report.requested_fonts}",
        f"- Missing fonts: {report.missing_fonts}",
        f"- Metric-compatible resolutions: {report.resolved_metric}",
        f"- Manual imports required: {report.manual_required}",
        f"- Unsafe resolutions: {report.unsafe}",
        "",
        "| Requested | Action | Recommended | Relation | Source | Risk |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for resolution in report.resolutions:
        candidate = resolution.recommended_candidate
        lines.append(
            "| {font} | {action} | {candidate} | {relation} | {source} | {risk} |".format(
                font=resolution.requested_family,
                action=resolution.recommended_action,
                candidate="-" if candidate is None else candidate.provided_family,
                relation="-" if candidate is None else candidate.relation,
                source="-" if candidate is None else candidate.source,
                risk=resolution.risk_level,
            )
        )
    return "\n".join(lines) + "\n"


def to_table(report: ResolutionReport) -> str:
    table = Table()
    table.add_column("Font")
    table.add_column("Action")
    table.add_column("Risk")
    table.add_column("Candidate")
    table.add_column("Source")
    table.add_column("Relation")
    table.add_column("Package")
    for resolution in report.resolutions:
        candidate = resolution.recommended_candidate
        table.add_row(
            resolution.requested_family,
            resolution.recommended_action,
            resolution.risk_level,
            "" if candidate is None else candidate.provided_family,
            "" if candidate is None else candidate.source,
            "" if candidate is None else candidate.relation,
            "" if candidate is None else candidate.package_name or "",
        )
    console = Console(record=True)
    console.print(table)
    return console.export_text()


def _candidate_to_dict(candidate) -> dict[str, Any] | None:
    if candidate is None:
        return None
    data = asdict(candidate)
    if candidate.install_command is not None:
        data["install_command"] = list(candidate.install_command)
    return data
