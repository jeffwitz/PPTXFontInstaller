Qt GUI
======

Launch the graphical interface with:

.. code-block:: bash

   pptx-font-resolver-gui

The GUI re‑uses the same analysis engine as the CLI and provides a visual interface for scanning, reviewing and resolving font issues.

.. contents::
   :local:

.. _gui-scan-view:

Scan View
---------

The default view scans a folder and displays the fonts used.

Interface elements:

+---------------------+--------------------------------------------------+
| Element             | Description                                      |
+=====================+==================================================+
| **Menu bar**        | File, Edit, View, Help                           |
+---------------------+--------------------------------------------------+
| **Toolbar**         | Quick‑action buttons: Scan, Stop, Export         |
+---------------------+--------------------------------------------------+
| **Folder selector** | Button to choose a folder to scan                |
+---------------------+--------------------------------------------------+
| **Depth**           | Dropdown (1, 2, infinite)                        |
+---------------------+--------------------------------------------------+
| **Number of jobs**  | Dropdown (1‑8)                                   |
+---------------------+--------------------------------------------------+
| **Filter to missing**| Checkbox to display only missing fonts          |
+---------------------+--------------------------------------------------+
| **Table**           | Shows fonts, status, occurrences and files      |
+---------------------+--------------------------------------------------+
| **Details panel**   | Shows detailed information for the selected row |
+---------------------+--------------------------------------------------+

Expected results:

* **Green** – Font installed exactly
* **Red** – Font not available via Fontist
* **Yellow** – Installation failed
* **Gray** – Ignored (session‑only)

.. note::
   Double‑click a row to view its details in the right‑hand panel.

.. _gui-resolution-view:

Resolution View
---------------

Switch to the **Resolution** tab to see multi‑source resolution recommendations.

Columns displayed:

+---------------------+--------------------------------------------------+
| Column              | Description                                      |
+=====================+==================================================+
| **Install**         | Checkbox to select a font for installation       |
+---------------------+--------------------------------------------------+
| **Family**          | Font family name                                 |
+---------------------+--------------------------------------------------+
| **Installed**       | ✓ if the font is installed exactly               |
+---------------------+--------------------------------------------------+
| **Fontist**         | ✓ if the font is available via Fontist           |
+---------------------+--------------------------------------------------+
| **Recommended action**| Action to take (Install via Fontist, Accept fallback, …) |
+---------------------+--------------------------------------------------+
| **Recommended family**| Suggested replacement family                    |
+---------------------+--------------------------------------------------+
| **Relation**        | Type of relation (exact, metric‑compatible, visual) |
+---------------------+--------------------------------------------------+
| **Risk**            | Risk level (Low, Medium, High)                  |
+---------------------+--------------------------------------------------+
| **Source**          | Source of recommendation (fontist, google, local) |
+---------------------+--------------------------------------------------+
| **Files**           | List of files using this font                   |
+---------------------+--------------------------------------------------+

Available actions (buttons at the top):

+-------------------------------------+--------------------------------------+
| Button                             | Action                               |
|=====================================|======================================|
| **Install via Fontist**             | Install the selected font via Fontist |
| **Install via Google Fonts**        | Install the selected font via Google Fonts |
| **Install system package**          | Install via the system package manager (apt) |
| **Install safe recommendations**    | Install all fonts marked as safe (Low/Medium risk) |
| **Import font file**                | Import a user‑provided font file |
| **Accept fallback**                 | Create a Fontconfig alias |
| **Ignore**                          | Ignore the font for this session |
| **Export**                          | Export the table (JSON, CSV, Markdown) |
|-------------------------------------+--------------------------------------|

.. note::
   - The **Install safe recommendations** button installs every font with a Low/Medium risk flag.
   - Action buttons are disabled until at least one row is selected.

Row colors after installation
------------------------------

After a successful installation the rows become **green** and display one of:

.. code-block:: text

   ✓ Installed via Fontist
   ✓ Installed via Google Fonts
   ✓ Imported

If an installation fails the row turns **yellow** and an error message appears in the details panel.

Details Panel
-------------

The right‑hand panel shows detailed information for the selected row:

- **Status** – Installed / Not installed / Substituted
- **Occurrences** – Number of times the font appears
- **Files** – List of files using the font
- **Recommendation** – Full recommendation description
- **Fontconfig alias** – If a fallback is active
- **Logs** – Error or warning messages

Example details output:

.. code-block:: text

   Family: Futura PT Bold
   Status: Not installed
   Occurrences: 5
   Files: pres1.pptx, pres2.pptx
   Recommendation: Accept fallback to Montserrat (visual)
   Fontconfig alias: Futura PT Bold → Montserrat
   Logs: Alias created successfully

Export
------

Both Scan and Resolution views can be exported in several formats:

- **JSON** – Raw data for automated processing
- **CSV** – Spreadsheet‑friendly table
- **Markdown** – Human‑readable report

To export:

1. Click the **Export** button (top‑right).
2. Choose the desired format.
3. Choose a destination path.
4. Click **Save**.

Sample Markdown export:

.. code-block:: markdown

   # Scan Report – 2026‑06‑24
   
   ## Summary
   - Folder: ~/Documents/Presentations
   - Unique fonts: 42
   - Missing fonts: 12
   
   ## Fonts
   
   | Family         | Status   | Occurrences | Files                     |
   |----------------|----------|-------------|---------------------------|
   | Calibri        | Missing  | 42          | pres1.pptx, pres2.pptx   |
   | Aptos          | Missing  | 12          | report.docx               |
   | Montserrat      | Installed| 8           | pres1.pptx                |
   | Futura PT Bold  | Substituted| 5         | pres3.pptx                |

Workers and task management
---------------------------

The GUI runs background workers for:

- Scanning folders
- Installing fonts
- Resolving recommendations

Workers start automatically when a task begins and are stopped cleanly when the window closes.

.. note::
   Closing the window while a worker is running may cause a crash. Allow workers to finish or click **Stop** before exiting.

Off‑screen mode (for CI tests)
------------------------------

Run the GUI without a display (useful for automated tests):

.. code-block:: bash

   env QT_QPA_PLATFORM=offscreen pptx-font-resolver-gui

The application will start, create the window in memory and then exit cleanly.

Tips & tricks
-------------

- **Sorting** – Click a column header to sort the table.
- **Search** – Use the search box at the top‑right to filter fonts.
- **Multi‑select** – Hold Ctrl/Cmd to select multiple rows.
- **Re‑scan** – After installing fonts, click **Re‑scan** to refresh the view.

See also
--------

- :doc:`gui-cas-pratiques` – Practical use‑cases for the GUI.
- :doc:`fallbacks` – Understanding Fontconfig fallbacks.
- :doc:`resolve-workflow` – Full end‑to‑end workflow.
- :doc:`troubleshooting` – Common issues and solutions.

