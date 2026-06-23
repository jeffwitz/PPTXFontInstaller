from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from pptx_font_resolver.fontconfig import clear_fontconfig_cache


class FontconfigAliasError(RuntimeError):
    pass


@dataclass(frozen=True)
class FontconfigAlias:
    requested_family: str
    fallback_family: str
    relation: str = "visual-substitute"
    source: str = "manual"


@dataclass(frozen=True)
class FontconfigAliasResult:
    alias: FontconfigAlias
    store_path: Path
    config_path: Path
    cache_refreshed: bool


def default_alias_store_path() -> Path:
    return _config_home() / "pptx-font-resolver" / "fontconfig-aliases.json"


def default_fontconfig_alias_path() -> Path:
    return _config_home() / "fontconfig" / "conf.d" / "90-pptx-font-resolver.conf"


def load_aliases(store_path: Path | None = None) -> tuple[FontconfigAlias, ...]:
    path = default_alias_store_path() if store_path is None else store_path
    if not path.exists():
        return ()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise FontconfigAliasError(f"Cannot read Fontconfig alias store: {exc}") from exc
    aliases: list[FontconfigAlias] = []
    for item in payload.get("aliases", []):
        requested = _clean_family(item.get("requested_family", ""))
        fallback = _clean_family(item.get("fallback_family", ""))
        if not requested or not fallback:
            continue
        aliases.append(
            FontconfigAlias(
                requested_family=requested,
                fallback_family=fallback,
                relation=str(item.get("relation") or "visual-substitute"),
                source=str(item.get("source") or "manual"),
            )
        )
    return tuple(sorted(aliases, key=lambda alias: alias.requested_family.casefold()))


def save_aliases(
    aliases: tuple[FontconfigAlias, ...],
    store_path: Path | None = None,
) -> Path:
    path = default_alias_store_path() if store_path is None else store_path
    path.parent.mkdir(parents=True, exist_ok=True)
    unique = _deduplicate_aliases(aliases)
    payload = {
        "version": 1,
        "aliases": [asdict(alias) for alias in unique],
    }
    _atomic_write(path, json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    return path


def write_fontconfig_aliases(
    aliases: tuple[FontconfigAlias, ...],
    config_path: Path | None = None,
) -> Path:
    path = default_fontconfig_alias_path() if config_path is None else config_path
    unique = _deduplicate_aliases(aliases)
    if not unique:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise FontconfigAliasError(f"Cannot remove Fontconfig alias file: {exc}") from exc
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write(path, _aliases_to_fontconfig_xml(unique))
    return path


def upsert_alias(
    alias: FontconfigAlias,
    *,
    store_path: Path | None = None,
    config_path: Path | None = None,
) -> tuple[FontconfigAlias, ...]:
    aliases = [item for item in load_aliases(store_path) if not _same_request(item, alias)]
    aliases.append(
        FontconfigAlias(
            requested_family=_clean_family(alias.requested_family),
            fallback_family=_clean_family(alias.fallback_family),
            relation=alias.relation,
            source=alias.source,
        )
    )
    unique = _deduplicate_aliases(tuple(aliases))
    save_aliases(unique, store_path)
    write_fontconfig_aliases(unique, config_path)
    return unique


def apply_fontconfig_alias(
    requested_family: str,
    fallback_family: str,
    *,
    relation: str = "visual-substitute",
    source: str = "manual",
    store_path: Path | None = None,
    config_path: Path | None = None,
    refresh_cache: bool = True,
) -> FontconfigAliasResult:
    alias = FontconfigAlias(
        requested_family=_clean_family(requested_family),
        fallback_family=_clean_family(fallback_family),
        relation=relation,
        source=source,
    )
    if not alias.requested_family or not alias.fallback_family:
        raise FontconfigAliasError("Requested and fallback font families are required.")
    upsert_alias(alias, store_path=store_path, config_path=config_path)
    cache_refreshed = refresh_fontconfig_cache() if refresh_cache else False
    return FontconfigAliasResult(
        alias=alias,
        store_path=default_alias_store_path() if store_path is None else store_path,
        config_path=default_fontconfig_alias_path() if config_path is None else config_path,
        cache_refreshed=cache_refreshed,
    )


def refresh_fontconfig_cache() -> bool:
    result = subprocess.run(
        ["fc-cache", "-f"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "fc-cache failed"
        raise FontconfigAliasError(detail)
    clear_fontconfig_cache()
    return True


def _aliases_to_fontconfig_xml(aliases: tuple[FontconfigAlias, ...]) -> str:
    lines = [
        '<?xml version="1.0"?>',
        "<!DOCTYPE fontconfig SYSTEM \"urn:fontconfig:fonts.dtd\">",
        "<fontconfig>",
        "  <!-- Managed by pptx-font-resolver. Edit the JSON store instead. -->",
    ]
    for alias in aliases:
        lines.extend(
            [
                "  <alias>",
                f"    <family>{escape(alias.requested_family)}</family>",
                "    <prefer>",
                f"      <family>{escape(alias.fallback_family)}</family>",
                "    </prefer>",
                "  </alias>",
            ]
        )
    lines.append("</fontconfig>")
    return "\n".join(lines) + "\n"


def _deduplicate_aliases(aliases: tuple[FontconfigAlias, ...]) -> tuple[FontconfigAlias, ...]:
    by_request: dict[str, FontconfigAlias] = {}
    for alias in aliases:
        cleaned = FontconfigAlias(
            requested_family=_clean_family(alias.requested_family),
            fallback_family=_clean_family(alias.fallback_family),
            relation=alias.relation,
            source=alias.source,
        )
        if not cleaned.requested_family or not cleaned.fallback_family:
            continue
        by_request[cleaned.requested_family.casefold()] = cleaned
    return tuple(sorted(by_request.values(), key=lambda alias: alias.requested_family.casefold()))


def _same_request(left: FontconfigAlias, right: FontconfigAlias) -> bool:
    return left.requested_family.casefold() == right.requested_family.casefold()


def _clean_family(family: str) -> str:
    return " ".join(str(family).split())


def _config_home() -> Path:
    configured = os.environ.get("XDG_CONFIG_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".config"


def _atomic_write(path: Path, content: str) -> None:
    tmp_path = path.with_name(f".{path.name}.tmp")
    try:
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.replace(path)
    except OSError as exc:
        raise FontconfigAliasError(f"Cannot write {path}: {exc}") from exc
