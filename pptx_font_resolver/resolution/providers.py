from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pptx_font_resolver import fontconfig
from pptx_font_resolver.fontist_backend import FontistBackend
from pptx_font_resolver.resolver import is_symbol_font

from .data import find_family_entry, load_json, normalize_family
from .google_fonts import lookup_google_font
from .models import FontCandidate


class FontProvider(Protocol):
    name: str

    def candidates_for(self, family: str) -> tuple[FontCandidate, ...]:
        ...


@dataclass
class LocalFontProvider:
    installed: set[str] | None = None
    name: str = "local"

    def __post_init__(self) -> None:
        if self.installed is None:
            try:
                self.installed = fontconfig.installed_families()
            except Exception:
                self.installed = set()

    def candidates_for(self, family: str) -> tuple[FontCandidate, ...]:
        installed = self.installed or set()
        if normalize_family(family) not in installed:
            return ()
        return (
            FontCandidate(
                requested_family=family,
                provided_family=family,
                source="local",
                relation="exact",
                installable=False,
                confidence=1.0,
            ),
        )


@dataclass
class FontistProvider:
    backend: FontistBackend | None = None
    accept_license: bool = False
    name: str = "fontist"

    def __post_init__(self) -> None:
        if self.backend is None:
            self.backend = FontistBackend()

    def candidates_for(self, family: str) -> tuple[FontCandidate, ...]:
        assert self.backend is not None
        probe = self.backend.probe_install(family)
        if not probe.available:
            return ()
        command = [
            "fontist",
            "install",
            "--newest",
            "--location",
            "user",
            "--update-fontconfig",
        ]
        if self.accept_license:
            command.append("--accept-all-licenses")
        command.append(family)
        return (
            FontCandidate(
                requested_family=family,
                provided_family=family,
                source="fontist",
                relation="exact",
                installable=True,
                confidence=0.95,
                install_command=tuple(command),
                license_hint="user license acceptance may be required",
            ),
        )


@dataclass(frozen=True)
class DistroPackageProvider:
    distro: str = "debian"
    name: str = "distro-package"

    def candidates_for(self, family: str) -> tuple[FontCandidate, ...]:
        match = find_family_entry(load_json("distro_packages.json"), family)
        if match is None:
            return ()
        requested, entry = match
        candidates: list[FontCandidate] = []
        for key in ("exact_or_family", "metric_compatible"):
            for item in entry.get(key, []):
                if item.get("distro", self.distro) not in {self.distro, "debian"}:
                    continue
                package = item.get("package")
                relation = item.get("relation", "metric-compatible")
                candidates.append(
                    FontCandidate(
                        requested_family=requested,
                        provided_family=item["family"],
                        source="distro-package",
                        relation=relation,
                        installable=bool(package),
                        confidence=0.9 if relation == "exact" else 0.82,
                        install_command=("sudo", "apt", "install", package)
                        if package
                        else None,
                        package_name=package,
                        license_hint=item.get("license"),
                    )
                )
        return tuple(candidates)


@dataclass(frozen=True)
class GoogleFontsProvider:
    live_lookup: bool = True
    timeout: float = 3.0
    name: str = "google-fonts"

    def candidates_for(self, family: str) -> tuple[FontCandidate, ...]:
        match = find_family_entry(load_json("google_fonts_index.json"), family)
        if match is not None:
            requested, entry = match
            provided_family = entry["family"]
            license_hint = entry.get("license")
            url = entry.get("url")
        elif self.live_lookup:
            info = lookup_google_font(family, timeout=self.timeout)
            if info is None:
                return ()
            requested = family
            provided_family = info.family
            license_hint = info.license_hint
            url = info.css_url
        else:
            return ()
        return (
            FontCandidate(
                requested_family=requested,
                provided_family=provided_family,
                source="google-fonts",
                relation="exact",
                installable=True,
                confidence=0.86,
                install_command=("pptx-font-resolver", "install-google-font", provided_family),
                license_hint=license_hint,
                url=url,
            ),
        )


@dataclass(frozen=True)
class CuratedFallbackProvider:
    name: str = "curated"

    def candidates_for(self, family: str) -> tuple[FontCandidate, ...]:
        match = find_family_entry(load_json("font_aliases.json"), family)
        if match is None:
            return ()
        requested, entry = match
        candidates: list[FontCandidate] = []
        for item in entry.get("metric_compatible", []):
            package = item.get("package")
            candidates.append(
                FontCandidate(
                    requested_family=requested,
                    provided_family=item["family"],
                    source=item.get("source", "curated"),
                    relation="metric-compatible",
                    installable=bool(package),
                    confidence=0.82,
                    install_command=("sudo", "apt", "install", package)
                    if package
                    else None,
                    package_name=package,
                    license_hint=item.get("license"),
                )
            )
        for item in entry.get("visual_substitute", []):
            candidates.append(
                FontCandidate(
                    requested_family=requested,
                    provided_family=item["family"],
                    source=item.get("source", "curated"),
                    relation="visual-substitute",
                    installable=False,
                    confidence=0.55,
                    warning="visual substitute only; layout metrics are not guaranteed",
                )
            )
        manual = entry.get("manual")
        if manual:
            candidates.append(
                FontCandidate(
                    requested_family=requested,
                    provided_family=requested,
                    source="manual",
                    relation="exact",
                    installable=False,
                    confidence=0.7,
                    license_hint=manual.get("note"),
                    warning=manual.get("note"),
                )
            )
        return tuple(candidates)


@dataclass(frozen=True)
class FontconfigFallbackProvider:
    name: str = "fontconfig"

    def candidates_for(self, family: str) -> tuple[FontCandidate, ...]:
        status = fontconfig.check_font(family)
        if not status.matched_family or status.exact_installed:
            return ()
        relation = "unsafe" if is_symbol_font(family) else "generic"
        return (
            FontCandidate(
                requested_family=family,
                provided_family=status.matched_family,
                source="fontconfig",
                relation=relation,
                installable=False,
                confidence=0.15 if relation == "unsafe" else 0.35,
                warning="Fontconfig substitution; review manually",
            ),
        )


@dataclass(frozen=True)
class ManualImportProvider:
    name: str = "manual"

    def candidates_for(self, family: str) -> tuple[FontCandidate, ...]:
        if not is_symbol_font(family):
            return ()
        warning = "Symbol font: automatic substitution may alter glyph semantics."
        return (
            FontCandidate(
                requested_family=family,
                provided_family=family,
                source="manual",
                relation="exact",
                installable=False,
                confidence=0.45,
                warning=warning,
            ),
        )
