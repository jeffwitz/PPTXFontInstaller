from __future__ import annotations

import builtins
import sys
import types

import pytest

from pptx_font_resolver.resolution.manual_import import (
    ManualImportError,
    import_font_file,
    iter_font_files,
    read_font_families,
)


class FakeNameRecord:
    def __init__(self, name_id: int, value: str) -> None:
        self.nameID = name_id
        self._value = value

    def toUnicode(self) -> str:
        return self._value


class FakeFont:
    def __getitem__(self, item: str):
        if item != "name":
            raise KeyError(item)
        return types.SimpleNamespace(
            names=[
                FakeNameRecord(1, "Fallback Family"),
                FakeNameRecord(16, "Preferred Family"),
            ]
        )

    def close(self) -> None:
        pass


def install_fake_fonttools(monkeypatch: pytest.MonkeyPatch) -> None:
    ttlib = types.ModuleType("fontTools.ttLib")
    ttlib.TTFont = lambda path: FakeFont()
    ttlib.TTCollection = lambda path: types.SimpleNamespace(fonts=[FakeFont()])
    package = types.ModuleType("fontTools")
    package.ttLib = ttlib
    monkeypatch.setitem(sys.modules, "fontTools", package)
    monkeypatch.setitem(sys.modules, "fontTools.ttLib", ttlib)


def test_iter_font_files_accepts_supported_extensions(tmp_path):
    root = tmp_path / "fonts"
    nested = root / "nested"
    nested.mkdir(parents=True)
    first = root / "A.ttf"
    second = nested / "B.OTF"
    ignored = root / "notes.txt"
    first.write_bytes(b"fake")
    second.write_bytes(b"fake")
    ignored.write_text("nope")

    assert iter_font_files(root) == (first, second)
    assert iter_font_files(root, recursive=False) == (first,)


def test_read_font_families_uses_preferred_family_name(tmp_path, monkeypatch):
    install_fake_fonttools(monkeypatch)
    font = tmp_path / "Demo.ttf"
    font.write_bytes(b"fake")

    assert read_font_families(font) == ("Preferred Family",)


def test_import_font_file_copies_to_target_and_refreshes_cache(tmp_path, monkeypatch):
    install_fake_fonttools(monkeypatch)
    calls = []
    monkeypatch.setattr(
        "pptx_font_resolver.resolution.manual_import.subprocess.run",
        lambda command, **kwargs: calls.append(command) or types.SimpleNamespace(returncode=0),
    )
    source = tmp_path / "Demo.ttf"
    target = tmp_path / "target"
    source.write_bytes(b"fake")

    result = import_font_file(source, target=target)

    assert result.family_names == ("Preferred Family",)
    assert result.target_path == target / "Demo.ttf"
    assert result.target_path.read_bytes() == b"fake"
    assert result.copied is True
    assert result.cache_refreshed is True
    assert calls == [["fc-cache", "-f", str(target)]]


def test_read_font_families_has_clear_error_when_fonttools_missing(tmp_path, monkeypatch):
    font = tmp_path / "Demo.ttf"
    font.write_bytes(b"fake")
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "fontTools.ttLib":
            raise ImportError("missing")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(ManualImportError, match="fontTools is required"):
        read_font_families(font)


def test_import_font_file_rejects_unsupported_extension(tmp_path):
    source = tmp_path / "Demo.txt"
    source.write_text("fake")

    with pytest.raises(ManualImportError, match="Unsupported font extension"):
        import_font_file(source)
