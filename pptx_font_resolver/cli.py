from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from .analysis import analyze_path
from .fontist_backend import FontistBackend, FontistInstallResult, output_mentions_license
from .report import to_csv, to_json, to_markdown, write_report
from .scanner import default_jobs

app = typer.Typer(help="Scan PPTX files and diagnose missing Linux fonts.")
console = Console()


@app.command()
def scan(
    folder: Annotated[Path, typer.Argument(help="Folder or PPTX file to scan.")],
    depth: Annotated[str, typer.Option(help="Depth integer or 'infinite'.")] = "infinite",
    jobs: Annotated[int, typer.Option(help="Parallel workers.")] = default_jobs(),
    format: Annotated[str, typer.Option(help="table or json.")] = "table",
) -> None:
    analysis = analyze_path(folder, depth=depth, jobs=jobs, use_fontconfig=False)
    if format == "json":
        console.print_json(to_json(analysis.scan, analysis.fonts))
        return
    if format != "table":
        raise typer.BadParameter("format must be table or json")
    embedded_count = sum(
        1 for document in analysis.scan.documents if document.embedded_font_entries
    )
    console.print(f"PPTX analysés : {analysis.documents_scanned}")
    console.print(f"Polices uniques : {analysis.unique_fonts}")
    console.print(f"PPTX invalides : {analysis.invalid_documents}")
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
    analysis = analyze_path(folder, depth=depth, jobs=jobs, use_fontconfig=True)
    summaries = analysis.fonts
    if only_missing:
        summaries = tuple(
            font for font in summaries if not (font.status and font.status.exact_installed)
        )
    elif not all_fonts:
        summaries = tuple(summaries)

    content = _format_output(format, analysis.scan, summaries, show_files=show_files)
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
    analysis = analyze_path(folder, depth=depth, jobs=jobs, use_fontconfig=True)
    content = _format_output(format, analysis.scan, analysis.fonts, show_files=True)
    if output is None:
        console.print(content)
    else:
        write_report(output, content)


@app.command("install-font")
def install_font(
    font_name: Annotated[str, typer.Argument(help="Font family to install.")],
    accept_license: Annotated[
        bool,
        typer.Option(help="Accept the license for this explicitly selected font."),
    ] = True,
    ask_license: Annotated[
        bool,
        typer.Option("--ask-license/--no-ask-license", help="Ask if Fontist requires a license."),
    ] = True,
    location: Annotated[
        str,
        typer.Option(help="Fontist install location: user or fontist."),
    ] = "user",
    dry_run: Annotated[bool, typer.Option(help="Probe but do not install.")] = False,
) -> None:
    backend = FontistBackend()
    location = _validate_install_location(location)
    _install_single_font(
        backend,
        font_name,
        accept_license=accept_license,
        ask_license=ask_license,
        location=location,
        dry_run=dry_run,
    )


@app.command("install-missing")
def install_missing(
    folder: Annotated[Path, typer.Argument(help="Folder or PPTX file to scan.")],
    depth: Annotated[str, typer.Option(help="Depth integer or 'infinite'.")] = "infinite",
    jobs: Annotated[int, typer.Option(help="Parallel workers.")] = default_jobs(),
    ask: Annotated[
        bool,
        typer.Option("--ask/--no-ask", help="Ask before installing each font."),
    ] = True,
    accept_license: Annotated[
        bool,
        typer.Option(help="Accept licenses for each font selected with the install prompt."),
    ] = True,
    ask_license: Annotated[
        bool,
        typer.Option("--ask-license/--no-ask-license", help="Ask if Fontist requires a license."),
    ] = True,
    location: Annotated[
        str,
        typer.Option(help="Fontist install location: user or fontist."),
    ] = "user",
    dry_run: Annotated[
        bool,
        typer.Option(help="Show installable fonts but do not install."),
    ] = False,
) -> None:
    if accept_license and not ask and not dry_run:
        raise typer.BadParameter(
            "install-missing cannot accept licenses without --ask confirmation per font"
        )

    analysis = analyze_path(folder, depth=depth, jobs=jobs, use_fontconfig=True)
    candidates = list(analysis.missing_fonts)
    if not candidates:
        console.print("Aucune police manquante détectée.")
        return

    risk_order = {"high": 0, "medium": 1, "low": 2, "unknown": 3, "none": 4}
    candidates.sort(key=lambda item: (risk_order.get(item.risk_level, 9), item.family.casefold()))

    backend = FontistBackend()
    location = _validate_install_location(location)
    install_all_remaining = False
    for font in candidates:
        probe = backend.probe_install(font.family)
        if not probe.available:
            console.print(f"[yellow]Ignorée[/yellow] {font.family}: non disponible via Fontist")
            continue
        console.print(
            f"{font.family}: risque={font.risk_level}, occurrences={font.occurrences}, "
            f"fichiers={len(font.files)}"
        )
        if dry_run:
            continue
        if ask and not install_all_remaining:
            choice = _install_choice(font.family, accept_license)
            if choice == "n":
                console.print(f"[yellow]Ignorée[/yellow] {font.family}")
                continue
            if choice == "a":
                install_all_remaining = True
        _install_single_font(
            backend,
            font.family,
            accept_license=accept_license,
            ask_license=ask_license,
            location=location,
            dry_run=False,
            raise_on_error=False,
        )


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


def _install_single_font(
    backend: FontistBackend,
    font_name: str,
    *,
    accept_license: bool,
    ask_license: bool,
    location: str,
    dry_run: bool,
    raise_on_error: bool = True,
) -> bool:
    probe = backend.probe_install(font_name)
    if probe.stderr:
        console.print(probe.stderr.strip())
    if not probe.available:
        return _handle_install_failure(1, raise_on_error)
    console.print(
        f"Fontist: {font_name} disponible"
        + (" déjà installée par Fontist" if probe.installed else "")
    )
    if dry_run:
        return True

    result = backend.install(
        font_name,
        accept_license=accept_license,
        location=location,
        update_fontconfig=True,
    )
    if result.installed:
        _print_install_success(result)
        return True

    combined = f"{result.stdout}\n{result.stderr}"
    if output_mentions_license(combined) and not accept_license and ask_license:
        console.print(combined.strip())
        if typer.confirm(f"Accepter la licence Fontist pour {font_name} et relancer ?"):
            accepted_result = backend.install(
                font_name,
                accept_license=True,
                location=location,
                update_fontconfig=True,
            )
            if accepted_result.installed:
                _print_install_success(accepted_result)
                return True
            console.print(accepted_result.stderr.strip() or accepted_result.stdout.strip())
            return _handle_install_failure(accepted_result.returncode or 1, raise_on_error)
        console.print(f"[yellow]Licence refusée[/yellow] {font_name}")
        return _handle_install_failure(1, raise_on_error)

    console.print(result.stderr.strip() or result.stdout.strip())
    return _handle_install_failure(result.returncode or 1, raise_on_error)


def _print_install_success(result: FontistInstallResult) -> None:
    console.print(f"[green]Installée[/green] {result.font_name}")
    status = result.post_install_status
    if status is not None:
        exact = "oui" if status.exact_installed else "non"
        matched = status.matched_family or "inconnu"
        console.print(f"Vérification Fontconfig: exact={exact}, fc-match={matched}")


def _handle_install_failure(code: int, raise_on_error: bool) -> bool:
    if raise_on_error:
        raise typer.Exit(code=code)
    return False


def _install_choice(font_name: str, accept_license: bool) -> str:
    return Prompt.ask(
        _install_confirm_message(font_name, accept_license),
        choices=["y", "a", "n"],
        default="y",
        show_choices=True,
    )


def _install_confirm_message(font_name: str, accept_license: bool) -> str:
    action = f"Installer {font_name} via Fontist en local utilisateur"
    if accept_license:
        action += " et accepter sa licence si Fontist la demande"
    return f"{action} ? [y=yes, a=all, n=no]"


def _validate_install_location(location: str) -> str:
    if location not in {"user", "fontist"}:
        raise typer.BadParameter(
            "location must be 'user' or 'fontist'; system installs are disabled"
        )
    return location
