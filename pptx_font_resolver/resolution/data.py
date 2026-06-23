from __future__ import annotations

import json
from functools import cache
from importlib import resources
from typing import Any

DATA_PACKAGE = "pptx_font_resolver.data"


def normalize_family(family: str) -> str:
    return " ".join(family.split()).casefold()


@cache
def load_json(name: str) -> dict[str, Any]:
    resource = resources.files(DATA_PACKAGE).joinpath(name)
    return json.loads(resource.read_text(encoding="utf-8"))


def find_family_entry(data: dict[str, Any], family: str) -> tuple[str, Any] | None:
    target = normalize_family(family)
    for key, value in data.items():
        if normalize_family(key) == target:
            return key, value
    return None
