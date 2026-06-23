from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from .analysis import analyze_path
from .fontist_backend import FontistBackend, FontistInstallResult, output_mentions_license
from .report import to_csv, to_json, to_markdown, write_report
from .resolution import default_engine
from .resolution.manual_import import (
    ManualFontImportResult,
    ManualImportError,
    import_font_path,
)
from .resolution.models import ResolutionReport
from .resolution.report import (
    to_csv as resolution_to_csv,
)
from .resolution.report import (
    to_json as resolution_to_json,
)
from .resolution.report import (
    to_markdown as resolution_to_markdown,
)
from .resolution.report import (
    to_table as resolution_to_table,
)
from .scanner import default_jobs

app = typer.Typer(help="Scan Office PPTX/DOCX files and diagnose missing Linux fonts.")
console = Console()


@app.command()
def scan(
    folder: Annotated[Path, typer.Argument(help="Folder, PPTX file, or DOCX file to scan.")],
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
    console.print(f"Documents analysés : {analysis.documents_scanned}")
    console.print(f"Polices uniques : {analysis.unique_fonts}")
    console.print(f"Documents invalides : {analysis.invalid_documents}")
    console.print(f"Polices embarquées détectées : {embedded_count}")


@app.command()
def fonts(
    folder: Annotated[Path, typer.Argument(help="Folder, PPTX file, or DOCX file to scan.")],
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
    folder: Annotated[Path, typer.Argument(help="Folder, PPTX file, or DOCX file to scan.")],
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


@app.command()
def resolve(
    folder: Annotated[Path, typer.Argument(help="Folder, PPTX file, or DOCX file to resolve.")],
    depth: Annotated[str, typer.Option(help="Depth integer or 'infinite'.")] = "infinite",
    jobs: Annotated[int, typer.Option(help="Parallel workers.")] = default_jobs(),
    format: Annotated[str, typer.Option(help="table, json, csv, or markdown.")] = "table",
    output: Annotated[Path | None, typer.Option(help="Resolution report output file.")] = None,
    all_fonts: Annotated[bool, typer.Option(help="Include exact installed fonts.")] = False,
    only_missing: Annotated[bool, typer.Option(help="Only include missing exact fonts.")] = False,
    only_actionable: Annotated[
        bool,
        typer.Option(help="Only include fonts with an action other than none."),
    ] = False,
    provider: Annotated[
        str,
        typer.Option(help="fontist, apt, google, manual, or all."),
    ] = "all",
    distro: Annotated[str, typer.Option(help="debian or ubuntu.")] = "debian",
    accept_license: Annotated[
        bool,
        typer.Option(help="Include license-accepting Fontist commands in the report."),
    ] = False,
) -> None:
    if provider not in {"fontist", "apt", "google", "manual", "all"}:
        raise typer.BadParameter("provider must be fontist, apt, google, manual, or all")
    if distro not in {"debian", "ubuntu"}:
        raise typer.BadParameter("distro must be debian or ubuntu")
    analysis = analyze_path(folder, depth=depth, jobs=jobs, use_fontconfig=False)
    engine = default_engine(provider=provider, distro=distro, accept_license=accept_license)
    resolution_report = engine.resolve_many(
        analysis.scan.unique_fonts,
        scanned_files=len(analysis.scan.documents),
    )
    resolutions = resolution_report.resolutions
    if only_missing or not all_fonts:
        resolutions = tuple(
            resolution for resolution in resolutions if not resolution.exact_installed
        )
    if only_actionable:
        resolutions = tuple(
            resolution for resolution in resolutions if resolution.recommended_action != "none"
        )
    if resolutions != resolution_report.resolutions:
        resolution_report = _filtered_resolution_report(resolution_report, resolutions)
    content = _format_resolution_output(format, resolution_report)
    if output is None:
        console.print(content)
    else:
        write_report(output, content)


@app.command()
def explain(
    font_name: Annotated[str, typer.Argument(help="Font family to explain.")],
    provider: Annotated[
        str,
        typer.Option(help="fontist, apt, google, manual, or all."),
    ] = "all",
    distro: Annotated[str, typer.Option(help="debian or ubuntu.")] = "debian",
    accept_license: Annotated[
        bool,
        typer.Option(help="Include license-accepting Fontist commands in the explanation."),
    ] = False,
) -> None:
    if provider not in {"fontist", "apt", "google", "manual", "all"}:
        raise typer.BadParameter("provider must be fontist, apt, google, manual, or all")
    engine = default_engine(provider=provider, distro=distro, accept_license=accept_license)
    resolution = engine.resolve_family(font_name)
    console.print(_format_explanation(resolution))


@app.command("import-font")
def import_font(
    font_file: Annotated[Path, typer.Argument(help="TTF, OTF, or TTC font file to import.")],
    target: Annotated[
        Path | None,
        typer.Option(help="Target font directory."),
    ] = None,
    refresh_cache: Annotated[
        bool,
        typer.Option("--refresh-cache/--no-refresh-cache", help="Refresh Fontconfig cache."),
    ] = True,
    check_again: Annotated[
        Path | None,
        typer.Option(help="Folder, PPTX file, or DOCX file to resolve again after import."),
    ] = None,
    dry_run: Annotated[bool, typer.Option(help="Read metadata but do not copy.")] = False,
    copy: Annotated[
        bool,
        typer.Option("--copy/--symlink", help="Copy the font file or create a symlink."),
    ] = True,
) -> None:
    _run_manual_import(
        font_file,
        target=target,
        recursive=False,
        refresh_cache=refresh_cache,
        check_again=check_again,
        dry_run=dry_run,
        copy=copy,
    )


@app.command("import-fonts")
def import_fonts(
    font_folder: Annotated[Path, typer.Argument(help="Folder containing TTF, OTF, or TTC files.")],
    target: Annotated[
        Path | None,
        typer.Option(help="Target font directory."),
    ] = None,
    recursive: Annotated[bool, typer.Option("--recursive/--no-recursive")] = True,
    dry_run: Annotated[bool, typer.Option(help="Read metadata but do not copy.")] = False,
    copy: Annotated[
        bool,
        typer.Option("--copy/--symlink", help="Copy font files or create symlinks."),
    ] = True,
    refresh_cache: Annotated[
        bool,
        typer.Option("--refresh-cache/--no-refresh-cache", help="Refresh Fontconfig cache."),
    ] = True,
    check_again: Annotated[
        Path | None,
        typer.Option(help="Folder, PPTX file, or DOCX file to resolve again after import."),
    ] = None,
) -> None:
    _run_manual_import(
        font_folder,
        target=target,
        recursive=recursive,
        refresh_cache=refresh_cache,
        check_again=check_again,
        dry_run=dry_run,
        copy=copy,
    )


@app.command("install-font")
def install_font(
    font_name: Annotated[str, typer.Argument(help="Font family to install.")],
    accept_license: Annotated[
        bool,
        typer.Option(help="Accept the license for this explicitly selected font."),
    ] = False,
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
    folder: Annotated[Path, typer.Argument(help="Folder, PPTX file, or DOCX file to scan.")],
    depth: Annotated[str, typer.Option(help="Depth integer or 'infinite'.")] = "infinite",
    jobs: Annotated[int, typer.Option(help="Parallel workers.")] = default_jobs(),
    ask: Annotated[
        bool,
        typer.Option("--ask/--no-ask", help="Ask before installing each font."),
    ] = True,
    accept_license: Annotated[
        bool,
        typer.Option(help="Accept licenses for each font selected with the install prompt."),
    ] = False,
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
    provider: Annotated[
        str,
        typer.Option(help="fontist, apt, google, or all."),
    ] = "fontist",
    execute: Annotated[
        bool,
        typer.Option(help="Execute non-Fontist install commands such as sudo apt install."),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option("--yes/--no-yes", help="Confirm a grouped non-Fontist installation."),
    ] = False,
    all_missing: Annotated[
        bool,
        typer.Option(
            "--all",
            help=(
                "Try every missing font after one global confirmation instead of "
                "asking per font."
            ),
        ),
    ] = False,
) -> None:
    if provider not in {"fontist", "apt", "google", "all"}:
        raise typer.BadParameter("provider must be fontist, apt, google, or all")
    if accept_license and not ask and not dry_run and not all_missing:
        raise typer.BadParameter(
            "install-missing cannot accept licenses without --ask confirmation per font"
        )
    if provider != "fontist":
        _install_missing_from_resolution(
            folder,
            depth=depth,
            jobs=jobs,
            provider=provider,
            dry_run=dry_run,
            execute=execute,
            yes=yes,
            accept_license=accept_license,
        )
        return

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
    report_rows: list[tuple[str, str, str]] = []

    if all_missing and not dry_run:
        message = "Installer toutes les polices manquantes disponibles via Fontist ?"
        if accept_license:
            message = (
                "Installer toutes les polices manquantes disponibles via Fontist "
                "et accepter leurs licences si Fontist les demande ?"
            )
        confirmed = typer.confirm(message)
        if not confirmed:
            console.print("[yellow]Installation annulée[/yellow]")
            return
        install_all_remaining = True

    for font in candidates:
        probe = backend.probe_install(font.family)
        if not probe.available:
            message = _fontist_unavailable_detail(probe.stdout, probe.stderr)
            console.print(
                f"[yellow]Ignorée[/yellow] {font.family}: non disponible via Fontist"
            )
            report_rows.append((font.family, "non installable", message))
            continue
        console.print(
            f"{font.family}: risque={font.risk_level}, occurrences={font.occurrences}, "
            f"fichiers={len(font.files)}"
        )
        if dry_run:
            report_rows.append((font.family, "disponible", "dry-run"))
            continue
        if ask and not install_all_remaining:
            choice = _install_choice(font.family, accept_license)
            if choice == "n":
                console.print(f"[yellow]Ignorée[/yellow] {font.family}")
                report_rows.append((font.family, "ignorée", "refus utilisateur"))
                continue
            if choice == "a":
                install_all_remaining = True
        installed = _install_single_font(
            backend,
            font.family,
            accept_license=accept_license,
            ask_license=ask_license,
            location=location,
            dry_run=False,
            raise_on_error=False,
        )
        report_rows.append(
            (
                font.family,
                "installée" if installed else "échec",
                "Fontist OK" if installed else "voir la sortie Fontist ci-dessus",
            )
        )

    _print_install_attempt_report(report_rows)


def _filtered_resolution_report(report: ResolutionReport, resolutions) -> ResolutionReport:
    return ResolutionReport(
        scanned_files=report.scanned_files,
        requested_fonts=len(resolutions),
        missing_fonts=sum(1 for resolution in resolutions if not resolution.exact_installed),
        resolved_exact=sum(1 for resolution in resolutions if resolution.exact_installed),
        resolved_metric=sum(
            1
            for resolution in resolutions
            if resolution.recommended_candidate is not None
            and resolution.recommended_candidate.relation == "metric-compatible"
        ),
        manual_required=sum(
            1
            for resolution in resolutions
            if resolution.recommended_action in {"manual_import", "unsafe_symbol_font"}
        ),
        unsafe=sum(1 for resolution in resolutions if resolution.risk_level == "high"),
        resolutions=resolutions,
    )


def _format_resolution_output(format_name: str, report) -> str:
    if format_name == "json":
        return resolution_to_json(report)
    if format_name == "csv":
        return resolution_to_csv(report)
    if format_name == "markdown":
        return resolution_to_markdown(report)
    if format_name == "table":
        return resolution_to_table(report)
    raise typer.BadParameter("format must be table, json, csv, or markdown")


def _format_explanation(resolution) -> str:
    lines = [
        f"Requested font: {resolution.requested_family}",
        "",
        "Exact font:",
    ]
    if resolution.exact_installed:
        lines.append("  Installed exactly.")
    else:
        lines.append("  Not installed.")
    recommended = resolution.recommended_candidate
    lines.extend(
        [
            "",
            "Recommended:",
            f"  Action: {resolution.recommended_action}",
            f"  Risk: {resolution.risk_level}",
        ]
    )
    if recommended is None:
        lines.append("  Candidate: none")
    else:
        lines.extend(
            [
                f"  Family: {recommended.provided_family}",
                f"  Relation: {recommended.relation}",
                f"  Source: {recommended.source}",
            ]
        )
        if recommended.package_name:
            lines.append(f"  Package: {recommended.package_name}")
        if recommended.install_command:
            lines.append(f"  Install command: {' '.join(recommended.install_command)}")
        if recommended.license_hint:
            lines.append(f"  License: {recommended.license_hint}")
        if recommended.warning:
            lines.append(f"  Warning: {recommended.warning}")
    if resolution.notes:
        lines.extend(["", "Notes:"])
        lines.extend(f"  {note}" for note in resolution.notes)
    return "\n".join(lines)


def _run_manual_import(
    path: Path,
    *,
    target: Path | None,
    recursive: bool,
    refresh_cache: bool,
    check_again: Path | None,
    dry_run: bool,
    copy: bool,
) -> None:
    try:
        results = import_font_path(
            path,
            target=target,
            recursive=recursive,
            dry_run=dry_run,
            copy=copy,
            refresh_cache=refresh_cache,
        )
    except ManualImportError as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(code=1) from exc
    _print_manual_import_report(results, dry_run=dry_run)
    if check_again is not None:
        resolve(check_again, format="table", all_fonts=True)


def _print_manual_import_report(
    results: tuple[ManualFontImportResult, ...],
    *,
    dry_run: bool,
) -> None:
    table = Table(title="Manual font import")
    table.add_column("File")
    table.add_column("Families")
    table.add_column("Target")
    table.add_column("Status")
    for result in results:
        if dry_run:
            status = "dry-run"
        elif result.copied:
            status = "copied"
        elif result.linked:
            status = "symlinked"
        else:
            status = "read"
        if result.cache_refreshed:
            status += " + fc-cache"
        table.add_row(
            str(result.source_path),
            ", ".join(result.family_names),
            str(result.target_path),
            status,
        )
    console.print(table)


def _install_missing_from_resolution(
    folder: Path,
    *,
    depth: str,
    jobs: int,
    provider: str,
    dry_run: bool,
    execute: bool,
    yes: bool,
    accept_license: bool,
) -> None:
    analysis = analyze_path(folder, depth=depth, jobs=jobs, use_fontconfig=False)
    engine_provider = "all" if provider == "all" else provider
    engine = default_engine(provider=engine_provider, accept_license=accept_license)
    resolution_report = engine.resolve_many(
        analysis.scan.unique_fonts,
        scanned_files=len(analysis.scan.documents),
    )
    rows = _resolution_install_actions(resolution_report)
    _print_resolution_install_actions(rows)
    if not rows:
        console.print("Aucune action installable détectée.")
        return
    if dry_run or not execute:
        console.print("Aucune commande exécutée. Ajouter --execute pour lancer l'installation.")
        return
    apt_packages = sorted(
        {
            package
            for _, source, package, _command in rows
            if source == "distro-package" and package
        },
        key=str.casefold,
    )
    if not apt_packages:
        console.print("[yellow]Aucun paquet apt exécutable dans les recommandations.[/yellow]")
        return
    if not yes and not typer.confirm(
        "Exécuter sudo apt install pour les paquets recommandés ?"
    ):
        console.print("[yellow]Installation annulée[/yellow]")
        return
    command = ["sudo", "apt", "install", *apt_packages]
    result = subprocess.run(command, check=False)
    if result.returncode != 0:
        raise typer.Exit(code=result.returncode)


def _resolution_install_actions(
    report: ResolutionReport,
) -> list[tuple[str, str, str, tuple[str, ...] | None]]:
    rows: list[tuple[str, str, str, tuple[str, ...] | None]] = []
    for resolution in report.resolutions:
        if resolution.exact_installed:
            continue
        candidate = resolution.recommended_candidate
        if candidate is None or not candidate.installable:
            continue
        rows.append(
            (
                resolution.requested_family,
                candidate.source,
                candidate.package_name or "",
                candidate.install_command,
            )
        )
    return rows


def _print_resolution_install_actions(
    rows: list[tuple[str, str, str, tuple[str, ...] | None]],
) -> None:
    table = Table(title="Resolution install actions")
    table.add_column("Font")
    table.add_column("Source")
    table.add_column("Package")
    table.add_column("Command")
    for family, source, package, command in rows:
        table.add_row(family, source, package, "" if command is None else " ".join(command))
    console.print(table)


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


def _fontist_unavailable_detail(stdout: str, stderr: str) -> str:
    return stderr.strip() or stdout.strip() or "a installer manuellement"


def _print_install_attempt_report(rows: list[tuple[str, str, str]]) -> None:
    if not rows:
        return
    table = Table(title="Rapport installation Fontist")
    table.add_column("Police")
    table.add_column("Resultat")
    table.add_column("Detail")
    colors = {
        "installée": "green",
        "disponible": "cyan",
        "non installable": "red",
        "échec": "red",
        "ignorée": "yellow",
    }
    for family, status, detail in rows:
        color = colors.get(status, "white")
        table.add_row(family, f"[{color}]{status}[/{color}]", detail)
    console.print(table)


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
