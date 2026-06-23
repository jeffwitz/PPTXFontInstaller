from __future__ import annotations

from pathlib import Path

from pptx_font_resolver.resolution.google_fonts import (
    GoogleFontInfo,
    css_url_for_family,
    extract_font_urls,
    install_google_font,
)
from pptx_font_resolver.resolution.providers import GoogleFontsProvider


def test_css_url_for_family_encodes_spaces():
    assert css_url_for_family("Source Sans 3").endswith("family=Source+Sans+3")


def test_extract_font_urls_deduplicates_css_urls():
    css = """
    @font-face { src: url(https://fonts.gstatic.com/s/demo/v1/a.woff2); }
    @font-face { src: url(https://fonts.gstatic.com/s/demo/v1/a.woff2); }
    @font-face { src: url(https://fonts.gstatic.com/s/demo/v1/b.woff2); }
    """

    assert extract_font_urls(css) == (
        "https://fonts.gstatic.com/s/demo/v1/a.woff2",
        "https://fonts.gstatic.com/s/demo/v1/b.woff2",
    )


def test_google_fonts_provider_live_lookup(monkeypatch):
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.providers.lookup_google_font",
        lambda family, timeout: GoogleFontInfo(
            family=family,
            css_url=f"https://fonts.googleapis.com/css2?family={family}",
            font_urls=("https://fonts.gstatic.com/s/demo/v1/a.woff2",),
        ),
    )

    candidate = GoogleFontsProvider().candidates_for("Merriweather")[0]

    assert candidate.provided_family == "Merriweather"
    assert candidate.source == "google-fonts"
    assert candidate.relation == "exact"
    assert candidate.install_command == (
        "pptx-font-resolver",
        "install-google-font",
        "Merriweather",
    )


def test_google_fonts_provider_skips_live_lookup_for_curated_alias(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.providers.lookup_google_font",
        lambda family, timeout: calls.append(family),
    )

    assert GoogleFontsProvider().candidates_for("Futura PT Bold") == ()
    assert calls == []


def test_install_google_font_dry_run_uses_download_targets(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.google_fonts.lookup_google_font",
        lambda family, timeout: GoogleFontInfo(
            family=family,
            css_url=f"https://fonts.googleapis.com/css2?family={family}",
            font_urls=("https://fonts.gstatic.com/s/demo/v1/a.woff2",),
        ),
    )

    result = install_google_font("Merriweather", target=tmp_path, dry_run=True)

    assert result.family == "Merriweather"
    assert result.downloaded is False
    assert result.target_paths == (tmp_path / "merriweather-1.woff2",)


def test_install_google_font_downloads_and_refreshes_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.google_fonts.lookup_google_font",
        lambda family, timeout: GoogleFontInfo(
            family=family,
            css_url=f"https://fonts.googleapis.com/css2?family={family}",
            font_urls=("https://fonts.gstatic.com/s/demo/v1/a.woff2",),
        ),
    )
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.google_fonts.download_font_file",
        lambda url, timeout: b"font-bytes",
    )
    calls: list[Path] = []
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.google_fonts.refresh_font_cache",
        lambda target: calls.append(target) or True,
    )

    result = install_google_font("Merriweather", target=tmp_path)

    assert result.downloaded is True
    assert result.cache_refreshed is True
    assert result.target_paths[0].read_bytes() == b"font-bytes"
    assert calls == [tmp_path]
