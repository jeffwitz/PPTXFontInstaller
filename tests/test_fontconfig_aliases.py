from __future__ import annotations

from types import SimpleNamespace

from pptx_font_resolver.resolution.fontconfig_aliases import (
    FontconfigAlias,
    apply_fontconfig_alias,
    load_aliases,
    write_fontconfig_aliases,
)


def test_write_fontconfig_aliases_generates_user_alias_xml(tmp_path):
    config_path = tmp_path / "conf.d" / "90-pptx-font-resolver.conf"

    write_fontconfig_aliases(
        (
            FontconfigAlias(
                requested_family="Futura PT Bold",
                fallback_family="Montserrat",
                relation="visual-substitute",
                source="google-fonts",
            ),
            FontconfigAlias(
                requested_family="A&B Sans",
                fallback_family="Noto <Sans>",
            ),
        ),
        config_path=config_path,
    )

    text = config_path.read_text(encoding="utf-8")
    assert "<fontconfig>" in text
    assert "<family>Futura PT Bold</family>" in text
    assert "<family>Montserrat</family>" in text
    assert "<family>A&amp;B Sans</family>" in text
    assert "<family>Noto &lt;Sans&gt;</family>" in text


def test_apply_fontconfig_alias_persists_json_and_refreshes_cache(monkeypatch, tmp_path):
    store_path = tmp_path / "pptx-font-resolver" / "fontconfig-aliases.json"
    config_path = tmp_path / "fontconfig" / "conf.d" / "90-pptx-font-resolver.conf"
    calls: list[list[str]] = []

    def fake_run(command, **_kwargs):
        calls.append(command)
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(
        "pptx_font_resolver.resolution.fontconfig_aliases.subprocess.run",
        fake_run,
    )
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.fontconfig_aliases.clear_fontconfig_cache",
        lambda: None,
    )

    result = apply_fontconfig_alias(
        "  Futura   PT Bold ",
        " Montserrat ",
        relation="visual-substitute",
        source="google-fonts",
        store_path=store_path,
        config_path=config_path,
    )

    assert result.alias.requested_family == "Futura PT Bold"
    assert result.alias.fallback_family == "Montserrat"
    assert result.cache_refreshed is True
    assert calls == [["fc-cache", "-f"]]
    assert load_aliases(store_path) == (
        FontconfigAlias(
            requested_family="Futura PT Bold",
            fallback_family="Montserrat",
            relation="visual-substitute",
            source="google-fonts",
        ),
    )
    assert "<family>Futura PT Bold</family>" in config_path.read_text(encoding="utf-8")


def test_upserting_alias_replaces_previous_fallback(monkeypatch, tmp_path):
    store_path = tmp_path / "aliases.json"
    config_path = tmp_path / "90-pptx-font-resolver.conf"

    monkeypatch.setattr(
        "pptx_font_resolver.resolution.fontconfig_aliases.refresh_fontconfig_cache",
        lambda: True,
    )

    apply_fontconfig_alias(
        "Futura PT Bold",
        "Jost",
        store_path=store_path,
        config_path=config_path,
    )
    apply_fontconfig_alias(
        "Futura PT Bold",
        "Montserrat",
        store_path=store_path,
        config_path=config_path,
    )

    aliases = load_aliases(store_path)
    assert len(aliases) == 1
    assert aliases[0].fallback_family == "Montserrat"
