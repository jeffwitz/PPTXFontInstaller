GUI Practical Cases
====================

This page demonstrates common workflows using the graphical interface.

.. contents::
   :local:

Case 1 – Install all missing fonts via Google Fonts
---------------------------------------------------

**Scenario**: You have 15 missing fonts, all of which are available on Google Fonts.

**Steps**:

1. Launch the GUI:

   .. code-block:: bash

      pptx-font-resolver-gui

2. Click **Choose folder** and select the folder containing your documents.
3. Check **Filter to missing fonts** to hide the already‑installed fonts.
4. Switch to the **Resolution** tab.
5. Click **Install via Google Fonts** (top‑right button).
6. A popup lists the fonts to be installed with three buttons:

   - **Yes** – install this font immediately
   - **Yes for all** – install every listed font
   - **No** – skip this font

7. Click **Yes for all**.
8. The scan restarts automatically; rows for installed fonts turn **green**.

**Expected result**:

- All missing fonts are now installed.
- Rows are green with a ✓ in the **Installed** column.
- A status bar confirms the number of fonts installed.

Tip: If a font appears **red**, it is not available via Google Fonts – consider using ``Import font file`` or ``Accept fallback``.

Case 2 – Accept a fallback for a symbol font
-------------------------------------------

**Scenario**: A presentation uses ``Wingdings``. You prefer to map it to an open‑source symbol font.

**Steps**:

1. In the **Resolution** tab locate the row with ``Wingdings``.
2. Column **Risk** shows **High**.
3. Column **Recommended action** shows ``Accept fallback``.
4. Click **Explain** to view details.
5. Click **Accept fallback**.
6. A confirmation dialog appears:

   .. code-block:: text

      Create a Fontconfig alias:
      Wingdings → Noto Sans Symbols
      
      ⚠️ This substitution may change the meaning of glyphs.
      Continue?

   Choose **Yes**.
7. The row becomes **green** and the details panel shows the generated alias file.

**Result**:

- LibreOffice renders the document using ``Noto Sans Symbols``.
- The original family name (``Wingdings``) stays unchanged in the PPTX file.

Case 3 – Install a specific font via Fontist
--------------------------------------------

**Scenario**: You want to install ``Aptos`` from Fontist.

**Steps**:

1. In the **Resolution** tab find the row for ``Aptos``.
2. Column **Fontist** shows a green check.
3. Column **Recommended action** reads ``Install via Fontist``.
4. Click **Install via Fontist**.
5. A popup asks for license acceptance:

   .. code-block:: text

      Install Aptos via Fontist?
      
      ⚠️ License: Apache 2.0
      Accept license and install?

   Click **Yes**.
6. Installation runs in the background; a notification appears when finished.
7. The row turns **green** with a ✓ in the **Installed** column.

Case 4 – Export a report for a colleague
---------------------------------------

**Scenario**: You need to share a font‑status report with a teammate.

**Steps**:

1. Switch to either the **Scan** or **Resolution** tab.
2. Click **Export** (top‑right).
3. Choose the export format: JSON, CSV or Markdown.
4. Select a destination path and click **Save**.

The exported file contains the same table you see in the GUI, ready to be emailed or version‑controlled.

Case 5 – Ignore a font temporarily (session‑only)
------------------------------------------------

**Scenario**: A missing font is not critical for now and you want to hide it.

**Steps**:

1. In the **Resolution** tab locate the unwanted font.
2. Click **Ignore**.
3. The row turns **gray** and is excluded from further actions.

**Note**: Ignored fonts are only hidden for the current session; they reappear after a new scan.

Case 6 – Import a user‑provided font file
----------------------------------------

**Scenario**: You have a legally owned ``FuturaPT.ttf`` file you want to use.

**Steps**:

1. Click **Import font file** (top‑right button).
2. A file dialog opens – select ``~/Downloads/FuturaPT.ttf``.
3. Choose **Copy** or **Symlink**.
4. Click **Import**.
5. A notification confirms successful import.
6. Re‑scan the folder; the imported font now appears as **installed**.

Case 7 – Resolve a CJK font issue
---------------------------------

**Scenario**: ``Noto Sans CJK SC Regular`` is substituted by ``Noto Sans`` (high risk).

**Steps**:

1. Find the row for ``Noto Sans CJK SC Regular``.
2. Column **Risk** shows **High**.
3. Column **Recommended action** suggests ``Install system package`` or ``Import font file``.
4. Click **Explain** for details.
5. Install the CJK package via the terminal:

   .. code-block:: bash

      sudo apt install fonts-noto-cjk

6. Re‑scan the folder – the row becomes **green** and the substitution disappears.

Case 8 – Run the GUI in off‑screen mode (CI)
--------------------------------------------

**Scenario**: You need to verify that the GUI starts without a display (e.g., in a CI pipeline).

**Command**:

.. code-block:: bash

   env QT_QPA_PLATFORM=offscreen pptx-font-resolver-gui

The application creates a hidden window, runs the initialization code and exits with status 0.

See also
--------

- :doc:`gui` – Full description of the GUI layout and actions.
- :doc:`fallbacks` – Explanation of Fontconfig fallbacks.
- :doc:`resolve-workflow` – End‑to‑end resolution process.
- :doc:`troubleshooting` – Common problems and solutions.

