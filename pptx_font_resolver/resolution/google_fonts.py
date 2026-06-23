from __future__ import annotations

import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .manual_import import default_import_target, refresh_font_cache

GOOGLE_FONTS_CSS_URL = "https://fonts.googleapis.com/css2"
CSS_URL_RE = re.compile(r"url\((https://[^)]+)\)")


class GoogleFontsError(RuntimeError):
    """Raised when a Google Fonts lookup or install cannot complete."""


@dataclass(frozen=True)
class GoogleFontInfo:
    family: str
    css_url: str
    font_urls: tuple[str, ...]
    license_hint: str = "See Google Fonts metadata for the selected family."


@dataclass(frozen=True)
class GoogleFontInstallResult:
    family: str
    target_paths: tuple[Path, ...]
    downloaded: bool
    cache_refreshed: bool


def css_url_for_family(family: str) -> str:
    query = urllib.parse.urlencode({"family": " ".join(family.split())})
    return f"{GOOGLE_FONTS_CSS_URL}?{query}"


def lookup_google_font(family: str, *, timeout: float = 5.0) -> GoogleFontInfo | None:
    normalized = " ".join(family.split())
    css_url = css_url_for_family(normalized)
    try:
        css = fetch_google_font_css(css_url, timeout=timeout)
    except GoogleFontsError:
        return None
    font_urls = extract_font_urls(css)
    if not font_urls:
        return None
    return GoogleFontInfo(family=normalized, css_url=css_url, font_urls=font_urls)


def fetch_google_font_css(css_url: str, *, timeout: float = 5.0) -> str:
    request = urllib.request.Request(
        css_url,
        headers={"User-Agent": "Mozilla/5.0 pptx-font-resolver"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        if exc.code == 400:
            raise GoogleFontsError("font family not found on Google Fonts") from exc
        raise GoogleFontsError(f"Google Fonts lookup failed: HTTP {exc.code}") from exc
    except OSError as exc:
        raise GoogleFontsError(f"Google Fonts lookup failed: {exc}") from exc


def extract_font_urls(css: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(CSS_URL_RE.findall(css)))


def install_google_font(
    family: str,
    *,
    target: Path | None = None,
    refresh_cache: bool = True,
    dry_run: bool = False,
    timeout: float = 10.0,
) -> GoogleFontInstallResult:
    info = lookup_google_font(family, timeout=timeout)
    if info is None:
        raise GoogleFontsError(f"{family} was not found on Google Fonts")
    target_dir = (target or default_import_target() / "google-fonts").expanduser()
    target_dir.mkdir(parents=True, exist_ok=True)
    target_paths = tuple(
        target_dir / _download_name(info.family, url, index)
        for index, url in enumerate(info.font_urls, start=1)
    )
    if dry_run:
        return GoogleFontInstallResult(
            family=info.family,
            target_paths=target_paths,
            downloaded=False,
            cache_refreshed=False,
        )
    for url, target_path in zip(info.font_urls, target_paths, strict=True):
        target_path.write_bytes(download_font_file(url, timeout=timeout))
    cache_refreshed = refresh_font_cache(target_dir) if refresh_cache else False
    return GoogleFontInstallResult(
        family=info.family,
        target_paths=target_paths,
        downloaded=True,
        cache_refreshed=cache_refreshed,
    )


def download_font_file(url: str, *, timeout: float = 10.0) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 pptx-font-resolver"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except OSError as exc:
        raise GoogleFontsError(f"Google Fonts download failed: {exc}") from exc


def _download_name(family: str, url: str, index: int) -> str:
    parsed = urllib.parse.urlparse(url)
    suffix = Path(parsed.path).suffix or ".woff2"
    slug = re.sub(r"[^A-Za-z0-9]+", "-", family).strip("-").lower()
    return f"{slug}-{index}{suffix}"
