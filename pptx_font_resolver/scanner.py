from __future__ import annotations

import os
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .models import PresentationFonts, ScanError, ScanResult
from .pptx_parser import parse_pptx


def default_jobs() -> int:
    cpu_count = os.cpu_count() or 1
    return min(8, cpu_count)


def parse_depth(depth: int | str | None) -> int | None:
    if depth is None or depth == "infinite":
        return None
    if isinstance(depth, int):
        if depth < 0:
            raise ValueError("depth must be >= 0 or 'infinite'")
        return depth
    try:
        value = int(depth)
    except ValueError as exc:
        raise ValueError("depth must be an integer or 'infinite'") from exc
    if value < 0:
        raise ValueError("depth must be >= 0 or 'infinite'")
    return value


def iter_pptx_paths(root: Path, depth: int | str | None = None) -> tuple[Path, ...]:
    paths, _errors = discover_pptx_paths(root, depth)
    return paths


def discover_pptx_paths(
    root: Path,
    depth: int | str | None = None,
) -> tuple[tuple[Path, ...], tuple[ScanError, ...]]:
    root = root.expanduser().resolve()
    max_depth = parse_depth(depth)
    if root.is_file():
        paths = (root,) if root.suffix.lower() == ".pptx" else ()
        return paths, ()
    if not root.exists():
        raise FileNotFoundError(root)

    paths: list[Path] = []
    errors: list[ScanError] = []
    stack: list[tuple[Path, int]] = [(root, 0)]
    while stack:
        directory, current_depth = stack.pop()
        try:
            entries = tuple(directory.iterdir())
        except OSError as exc:
            errors.append(ScanError(path=directory, message=str(exc)))
            continue
        for entry in entries:
            try:
                if entry.is_file() and entry.suffix.lower() == ".pptx":
                    paths.append(entry)
                elif entry.is_dir() and (max_depth is None or current_depth < max_depth):
                    stack.append((entry, current_depth + 1))
            except OSError as exc:
                errors.append(ScanError(path=entry, message=str(exc)))
    return (
        tuple(sorted(paths, key=lambda path: str(path).casefold())),
        tuple(sorted(errors, key=lambda error: str(error.path).casefold())),
    )


def scan_folder(
    root: Path,
    *,
    depth: int | str | None = "infinite",
    jobs: int | None = None,
) -> ScanResult:
    root = root.expanduser().resolve()
    paths, walk_errors = discover_pptx_paths(root, depth)
    if not paths:
        return ScanResult(root=root, documents=(), errors=walk_errors)

    worker_count = jobs or default_jobs()
    worker_count = max(1, min(worker_count, len(paths)))
    documents: list[PresentationFonts] = []
    errors: list[ScanError] = list(walk_errors)

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = {executor.submit(parse_pptx, path): path for path in paths}
        for future in as_completed(futures):
            path = futures[future]
            try:
                documents.append(future.result())
            except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
                errors.append(ScanError(path=path, message=str(exc)))

    return ScanResult(
        root=root,
        documents=tuple(sorted(documents, key=lambda document: str(document.path).casefold())),
        errors=tuple(sorted(errors, key=lambda error: str(error.path).casefold())),
    )

