from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from .report import to_csv, to_json, to_markdown, write_report
from .resolver import build_font_report
from .scanner import default_jobs, scan_folder

app = typer.Typer(help="Scan PPTX files and diagnose missing Linux fonts.")
console = Console()


@app.command()
def scan(
    folder: Annotated[Path, typer.Argument(help="Folder or PPTX file to scan.")],
    depth: Annotated[str, typer.Option(help="Depth integer or 'infinite'.")] = "infinite",
    jobs: Annotated[int, typer.Option(help="Parallel workers.")] = default_jobs(),
    format: Annotated[str, typer.Option(help="table or json.")] = "table",
) -> None:
    result = scan_folder(folder, depth=depth, jobs=jobs)
    fonts = build_font_report(result, use_fontconfig=False)
    if format == "json":
        console.print_json(to_json(result, fonts))
        return
    if format != "table":
        raise typer.BadParameter("format must be table or json")
    embedded_count = sum(1 for document in result.documents if document.embedded_font_entries)
    console.print(f"PPTX analysés : {len(result.documents)}")
    console.print(f"Polices uniques : {len(fonts)}")
    console.print(f"PPTX invalides : {len(result.errors)}")
    console.print(f"Polices embarquées détectées : {embedded_count}")


@app.command()
def fonts(
    folder: Annotated[Path, typer.Argument(help="Folder or PPTX file to scan.")],
    depth: Annotated[str, typer.Option(help="Depth integer or 'infinite'.")] = "infinite",
    jobs: Annotated[int, typer.Option(help="Parallel workers.")] = default_jobs(),
    format: Annotated[str, typer.Option(help="table, json, or csv.")] = "table",
    output: Annotated[Path | None, typer.Option(help="Optional output file.")] = None,
    show_files: Annotated[bool, typer.Option(help="Show files for each font.")] = False,
    all_fonts: Annotated[
        bool,
        typer.Option(help="Show all fonts, including exact installed."),
    ] = False,
    only_missing: Annotated[
        bool,
        typer.Option(help="Only show fonts not exactly installed."),
    ] = False,
) -> None:
    result = scan_folder(folder, depth=depth, jobs=jobs)
    summaries = build_font_report(result, use_fontconfig=True)
    if only_missing:
        summaries = tuple(
            font for font in summaries if not (font.status and font.status.exact_installed)
        )
    elif not all_fonts:
        summaries = tuple(summaries)

    content = _format_output(format, result, summaries, show_files=show_files)
    if output is not None:
        write_report(output, content)
    else:
        console.print(content)


@app.command()
def report(
    folder: Annotated[Path, typer.Argument(help="Folder or PPTX file to scan.")],
    depth: Annotated[str, typer.Option(help="Depth integer or 'infinite'.")] = "infinite",
    jobs: Annotated[int, typer.Option(help="Parallel workers.")] = default_jobs(),
    format: Annotated[str, typer.Option(help="json, csv, or markdown.")] = "json",
    output: Annotated[Path | None, typer.Option(help="Report output file.")] = None,
) -> None:
    result = scan_folder(folder, depth=depth, jobs=jobs)
    summaries = build_font_report(result, use_fontconfig=True)
    content = _format_output(format, result, summaries, show_files=True)
    if output is None:
        console.print(content)
    else:
        write_report(output, content)


def _format_output(format_name: str, result, summaries, *, show_files: bool) -> str:
    if format_name == "json":
        return to_json(result, summaries)
    if format_name == "csv":
        return to_csv(summaries)
    if format_name == "markdown":
        return to_markdown(result, summaries)
    if format_name == "table":
        return _plain_table(summaries, show_files=show_files)
    raise typer.BadParameter("format must be table, json, csv, or markdown")


def _plain_table(summaries, *, show_files: bool) -> str:
    table = Table()
    table.add_column("Police")
    table.add_column("Statut exact")
    table.add_column("Substitution Fontconfig")
    table.add_column("Risque")
    table.add_column("Occurrences", justify="right")
    table.add_column("Fichiers", justify="right")
    table.add_column("Recommandation")
    for font in summaries:
        status = font.status
        exact = (
            "inconnue"
            if status is None
            else ("installée" if status.exact_installed else "non installée")
        )
        match = "" if status is None else status.matched_family or ""
        table.add_row(
            font.family,
            exact,
            match,
            font.risk_level,
            str(font.occurrences),
            str(len(font.files)),
            font.recommendation,
        )
        if show_files:
            for file_path in font.files:
                table.add_row("", "", "", "", "", str(file_path), "")
    console = Console(record=True)
    console.print(table)
    return console.export_text()
