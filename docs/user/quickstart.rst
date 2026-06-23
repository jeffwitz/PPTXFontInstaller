Quickstart
==========

You have missing‑font issues in your PowerPoint or Word files on Linux? This guide will get you started in **three steps**.

.. contents::
   :local:

Step 1 – Install
--------------------

Install the package with the optional GUI dependencies:

.. code-block:: bash

   # From the PPTXFontInstaller repository
   pip install -e ".[dev,gui]"

   # Verify the installation
   pptx-font-resolver --help
   pptx-font-resolver-gui --help

.. note::
   - ``dev`` installs ``pytest`` and ``ruff`` for testing and linting.
   - ``gui`` installs ``PySide6`` for the Qt interface.
   - If you do not need the GUI, use ``pip install -e ".[dev,font-import]"``.

Step 2 – Scan your documents
-------------------------------

Scan a folder containing your PowerPoint (``.pptx``) or Word (``.docx``) files:

.. code-block:: bash

   # Scan a folder (infinite depth)
   pptx-font-resolver scan ~/Documents/Presentations --depth infinite

   # List all discovered fonts
   pptx-font-resolver fonts ~/Documents/Presentations --all-fonts --show-files

Expected result (example):

.. code-block:: text

   Family         | Status      | Occurrences | Files
   ---------------+-------------+------------+--------------------------------------
   Calibri        | Missing     | 42         | pres1.pptx, pres2.pptx
   Aptos          | Missing     | 12         | report.docx
   Montserrat      | Installed   | 8          | pres1.pptx
   Futura PT Bold  | Substituted | 5          | pres3.pptx

Step 3 – Resolve missing fonts
-----------------------------------

Generate a multi‑source resolution report to see the available options:

.. code-block:: bash

   pptx-font-resolver resolve ~/Documents/Presentations --provider all --format table

Expected result (example):

.. code-block:: text

   Family         | Installed | Fontist | Recommended action       | Relation
   ---------------+-----------+---------+------------------------+----------
   Calibri        | ✗       | ✓      | Install via Fontist    | exact
   Aptos          | ✗       | ✗      | Install via Google Fonts | visual
   Futura PT Bold  | ✗       | ✗      | Accept fallback        | visual

Install fonts via Google Fonts (example):

.. code-block:: bash

   # Dry‑run preview (no download)
   pptx-font-resolver install-missing ~/Documents/Presentations \
       --provider google --dry-run

   # Execute the installations
   pptx-font-resolver install-missing ~/Documents/Presentations \
       --provider google --execute --yes

Accept a fallback for a missing font (example):

.. code-block:: bash

   pptx-font-resolver accept-fallback "Futura PT Bold" "Montserrat"

   # Verify the alias is active
   fc-match "Futura PT Bold"

Expected result:

.. code-block:: text

   Montserrat: "Montserrat:style=Regular"

.. note::
   - Fonts installed via Google Fonts are placed in ``~/.local/share/fonts/pptx-font-installer/google-fonts/``.
   - Fontconfig aliases are written to ``~/.config/fontconfig/conf.d/90-pptx-font-resolver.conf``.
   - After any installation run ``fc-cache -f`` to refresh the cache.

Common use cases
-----------------

**Just want to see which fonts are used?**

.. code-block:: bash

   pptx-font-resolver fonts ./documents --format json --output fonts.json

**Need a list of missing fonts?**

.. code-block:: bash

   pptx-font-resolver resolve ./documents --provider all --format markdown \
       | grep "✗ Missing"

**Prefer the graphical interface?**

.. code-block:: bash

   pptx-font-resolver-gui

   # Or off‑screen mode for CI tests
   env QT_QPA_PLATFORM=offscreen pptx-font-resolver-gui

Next steps
----------

- **GUI**: See :doc:`gui` for a guided tour of the interface.
- **Fallbacks**: See :doc:`fallbacks` to understand and manage Fontconfig aliases.
- **Advanced resolution**: See :doc:`resolve-workflow` for a complete workflow.
- **Troubleshooting**: See :doc:`troubleshooting` if any issue occurs.

Full example
------------

Here is a complete example for a folder of presentations:

.. code-block:: bash

   # 1. Install
   pip install -e ".[dev,gui]"

   # 2. Scan
   pptx-font-resolver scan ~/CNRS/Presentations --depth infinite

   # 3. Resolve via Google Fonts
   pptx-font-resolver resolve ~/CNRS/Presentations --provider google --format table
   pptx-font-resolver install-missing ~/CNRS/Presentations \
       --provider google --execute --yes

   # 4. Accept remaining fallbacks
   pptx-font-resolver accept-fallback "Futura PT Bold" "Montserrat"
   pptx-font-resolver accept-fallback "ElsevierGulliver" "Source Serif 4"

   # 5. Verify
   pptx-font-resolver fonts ~/CNRS/Presentations --all-fonts

Result: all fonts are either installed or substituted.

