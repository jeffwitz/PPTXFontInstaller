# pptx-font-resolver

`pptx-font-resolver` scans PowerPoint `.pptx` files on Linux and reports which
fonts they use, whether those fonts are installed exactly, and which Fontconfig
substitutions or metric-compatible fallbacks are available.

The first target is reliable CLI behavior for large folders of presentations.
The local web interface will reuse the same Python core later.

## Install for development

```bash
python -m pip install -e ".[dev]"
```

## Commands

```bash
pptx-font-resolver scan ./slides --depth infinite
pptx-font-resolver fonts ./slides --all-fonts --show-files
pptx-font-resolver report ./slides --format json --output report.json
pptx-font-resolver install-font "Aptos" --location user
pptx-font-resolver install-missing ./slides --ask --location user
```

No font is downloaded or installed automatically. Fontist installation support
is intentionally interactive and requires explicit license acceptance.

## Current scope

- recursive `.pptx` discovery with bounded or infinite depth;
- ZIP-based PPTX parsing without extracting archives to disk;
- fast `typeface="..."` extraction from relevant PowerPoint XML entries;
- theme placeholder resolution for `+mn-lt`, `+mj-lt`, `+mn-ea`, `+mj-ea`,
  `+mn-cs`, and `+mj-cs`;
- embedded font presence detection through `ppt/fonts/*`;
- aggregate table, JSON, CSV, and Markdown reporting primitives;
- Fontconfig status checks and metric-compatible fallback hints.
- Risk classification for dangerous substitutions, including symbol fonts and
  CJK fonts substituted by Latin families.
- Conservative style-suffix normalization, such as treating
  `Noto Sans CJK SC Regular` as installed when `Noto Sans CJK SC` is present.
- Fontist-backed local user installation commands with dry-run and per-font
  confirmation support.
