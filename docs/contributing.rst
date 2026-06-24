Contributing
============

Thank you for your interest in contributing to ``pptx-font-resolver``!  This page explains how to set up a development environment, follow the project's conventions, and submit changes.

.. contents::
   :local:

.. _dev-setup:

Development environment setup
-----------------------------

1. **Clone the repository** (if you haven't already):

   .. code-block:: bash

      git clone https://github.com/<your-username>/PPTXFontInstaller.git
      cd PPTXFontInstaller

2. **Create a virtual environment**:

   .. code-block:: bash

      python -m venv .venv
      source .venv/bin/activate

3. **Install the package in development mode**:

   .. code-block:: bash

      pip install -e ".[dev,gui,font-import]"

   .. note::
      - ``dev`` installs ``pytest`` and ``ruff`` for testing and linting.
      - ``gui`` installs ``PySide6`` for the Qt interface.
      - ``font-import`` installs ``fonttools`` for reading font metadata.

4. **Verify the installation**:

   .. code-block:: bash

      pptx-font-resolver --help
      pptx-font-resolver-gui --help
      pytest --version
      ruff --version

.. _validation-before-commit:

Validation before commit
------------------------

Before pushing a change, run the following commands to ensure everything works:

.. code-block:: bash

   # 1. Linting (no errors)
   ruff check .

   # 2. Tests (all must pass)
   pytest -q

   # 3. Compile all Python modules (no syntax errors)
   python -m compileall pptx_font_resolver tests

   # 4. Build the documentation (no errors or critical warnings)
   sphinx-build -b html docs docs/_build/html

.. note::
   - ``ruff check .`` should return **0 problems**.
   - ``pytest -q`` should report **all tests passed**.
   - ``compileall`` must finish without error.
   - ``sphinx-build`` must complete without critical warnings.

.. _code-conventions:

Code conventions
----------------

1. **Naming**:
   - Modules: ``snake_case.py`` (e.g. ``fontconfig.py``)
   - Classes: ``PascalCase`` (e.g. ``FontScanner``)
   - Functions: ``snake_case()`` (e.g. ``scan_folder()``)
   - Variables: ``snake_case`` (e.g. ``font_family``)

2. **Docstrings**:
   - Use **Google** or **NumPy** style.
   - Example (Google style)::

      def scan_folder(path: str, depth: int, jobs: int) -> list[FileEntry]:
          """Scan a folder for Office files.

          Args:
              path: The folder to scan.
              depth: Recursion depth (integer or "infinite").
              jobs: Number of parallel workers.

          Returns:
              A list of scanned file entries.
          """

   - Example (NumPy style)::

      def resolve_font(family: str) -> FontResolution:
          """Resolve a font family to a recommended action.

          Parameters
          ----------
          family : str
              The font family name to resolve.

          Returns
          -------
          FontResolution
              The resolution object with recommended action.
          """

3. **Typing**: Use native Python types and ``typing`` where appropriate, e.g. ``def scan_folder(path: str, depth: int | str) -> list[FileEntry]:``.

4. **Error handling**: Raise specific exceptions (``ValueError``, ``FileNotFoundError``) and avoid catching generic ``Exception`` unless absolutely necessary. Log errors with the standard ``logging`` module.

5. **Imports**: Group imports by category:

   .. code-block:: python

      # Standard library
      import os
      import zipfile

      # Third‑party
      from typer import Typer
      from rich.console import Console

      # Local application
      from pptx_font_resolver.models import FileEntry

.. _tests-guidelines:

Test guidelines
----------------

1. **Coverage**: Every public function should have a test. Critical modules include ``scanner``, ``resolution/engine``, ``fontconfig`` and ``qt_app``. Aim for **100 % of public APIs** covered.
2. **Structure**: Tests live in ``tests/`` and follow the ``test_<module>.py`` naming convention.
3. **Fixtures**: Use ``conftest.py`` for shared fixtures such as temporary font directories.
4. **Test cases**: Cover normal operation, edge cases (corrupt files, missing fonts, substitution), and error handling.
5. **GUI tests**: Run with ``QT_QPA_PLATFORM=offscreen`` to avoid opening a window.

Example test (Google style)::

   def test_scan_folder(tmp_path):
       """Test that ``scan_folder`` discovers ``.pptx`` and ``.docx`` files."""
       (tmp_path / "pres.pptx").touch()
       (tmp_path / "doc.docx").touch()
       results = scan_folder(str(tmp_path), depth=1, jobs=1)
       assert len(results) == 2
       assert any(r.path.endswith("pres.pptx") for r in results)
       assert any(r.path.endswith("doc.docx") for r in results)

.. _commit-guidelines:

Commit guidelines
-----------------

1. **Commit message**:
   - Format: ``[type] Short description``
   - Types: ``feat``, ``fix``, ``docs``, ``test``, ``refactor``, ``chore``.
   - Example::

      [feat] Add CLI command to list Fontconfig fallbacks

2. **Scope**: Keep each commit focused on a single logical change.
3. **Branching**: Work directly on ``main``; push when the change is ready and passes all checks.

.. _pr-guidelines:

Pull‑request guidelines
-----------------------

1. **Title**: Use the same ``[type] Description`` format as the commit.
2. **Description**: Explain **why** the change is needed, list **what** was changed, and reference any related issues (e.g. ``Closes #123``).
3. **Validation**: Ensure the CI pipeline passes (lint, tests, documentation build).
4. **Review**: At least one other contributor must approve the PR before merging.
5. **Merge method**: Use ``squash`` to keep a clean history.

.. _publishing:

Publishing a new release
------------------------

1. **Bump the version** in ``pyproject.toml`` (e.g. ``0.1.1``).
2. **Build the package**:

   .. code-block:: bash

      pip install hatch
      hatch build

3. **Publish to PyPI**:

   .. code-block:: bash

      hatch publish

4. **Create a Git tag** and push it:

   .. code-block:: bash

      git tag v0.1.1
      git push origin v0.1.1

5. **Update ``CHANGELOG.md``** with a brief summary of changes.

.. _resources:

Resources
---------

- **Official documentation**: https://pptx-font-resolver.readthedocs.io/
- **GitHub repository**: https://github.com/jeffwitz/PPTXFontInstaller
- **Issues**: https://github.com/jeffwitz/PPTXFontInstaller/issues
- **Discussions**: https://github.com/jeffwitz/PPTXFontInstaller/discussions

.. _faq-dev:

Developer FAQ
-------------

**How do I debug a failing test?**

.. code-block:: bash

   pytest -xvs tests/test_scanner.py::test_scan_folder

**How do I test the GUI without a display?**

.. code-block:: bash

   env QT_QPA_PLATFORM=offscreen pytest -xvs tests/test_qt_app.py

**How do I add a new development dependency?**

1. Add it to the appropriate extra in ``pyproject.toml`` (``dev``, ``gui`` or ``font-import``).
2. Run ``pip install -e .[dev]`` (or the relevant extra) to install it locally.
3. Add tests if the dependency adds new functionality.

**How do I contribute to the documentation?**

Edit the ``.rst`` files under ``docs/`` and rebuild with ``sphinx-build -b html docs docs/_build/html``.  Commit with a ``[docs]`` prefix.

.. _commands-summary:

Summary of useful commands
--------------------------

+-------------------------------------+--------------------------------------+
| Goal                               | Command                               |
|=====================================|======================================|
| Install development environment      | pip install -e ".[dev,gui,font-import]" |
| Run all tests                       | pytest -q                            |
| Run the linter                      | ruff check .                         |
| Build the documentation             | sphinx-build -b html docs docs/_build/html |
| Test the GUI offscreen              | env QT_QPA_PLATFORM=offscreen pptx-font-resolver-gui |
| Verify imports                      | python -m compileall pptx_font_resolver tests |
|-------------------------------------+--------------------------------------|

If you have any questions, feel free to open a **discussion** on GitHub or contact the maintainer.

