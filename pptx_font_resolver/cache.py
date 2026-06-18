from __future__ import annotations

from pathlib import Path


def default_cache_path() -> Path:
    return Path.home() / ".cache" / "pptx-font-resolver" / "index.sqlite"

