# Contributing

## Development setup

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## Validation

Run these before opening a pull request:

```bash
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall pptx_font_resolver tests
```

## Safety rules

- Do not download fonts from unofficial sources.
- Do not install proprietary fonts without explicit user action.
- Do not accept Fontist licenses automatically for multiple fonts.
- Do not extract embedded PPTX fonts by default.

