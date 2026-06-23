Glossary
========

Definitions of the technical terms used throughout the documentation and the application.

.. contents::
   :local:

.. glossary::

   metric-compatible
      A font whose **metrics** (character width, spacing, line height) are similar to the original font.

      *Why?* → Fewer layout changes when substituting.
      *Example*: Carlito for Calibri, Caladea for Cambria.
      *Relation*: ``metric‑compatible`` appears in resolution reports.

   visual fallback
      A font that looks visually similar but has different metrics.

      *Why?* → Open‑source alternative when the exact font is unavailable.
      *Risk*: May alter line breaks and pagination.
      *Example*: Montserrat for Futura PT Bold.

   Fontconfig alias
      A local rule that maps one font family to another at the system level.

      *Location*: ``~/.config/fontconfig/conf.d/90-pptx-font-resolver.conf``.
      *Example*::

         <alias>
           <family>Futura PT Bold</family>
           <prefer>
             <family>Montserrat</family>
           </prefer>
         </alias>

      *Command*: ``pptx-font-resolver accept-fallback "Futura PT Bold" "Montserrat"``

   OOXML
      Office Open XML – the file format for ``.pptx`` and ``.docx`` files.

      *Structure*: A ZIP archive containing XML files (e.g. ``/ppt/slides/slide1.xml``).
      *Why?* → Allows scanning fonts without extracting the archive to disk.

   Fontist
      Command‑line tool that installs TrueType fonts (``.ttf``) from open‑source sources.

      *Usage*: ``pptx-font-resolver install-font "Aptos" --accept-license``
      *Limitation*: Proprietary fonts are often not available.

   Fontconfig
      Linux font management system that can:

      - Detect installed fonts
      - Provide substitution rules (e.g. Arial → Liberation Sans)
      - Store local aliases

      *Useful commands*::

         fc-list | grep "Montserrat"   # list fonts
         fc-match "Futura PT Bold"     # test substitution
         fc-cache -f                    # refresh cache

   Embedded font
      A font file that is bundled directly inside a ``.pptx`` or ``.docx`` document.

      *Detection*: ``pptx-font-resolver fonts ./documents --show-files``
      *Benefit*: No system‑wide installation required.
      *Limitation*: Some applications (e.g. LibreOffice) may ignore embedded fonts.

   Substitution / fallback
      When the requested font is unavailable, Fontconfig chooses an alternative.

      *Types*:

      - **Exact** – same family and style (e.g. Arial → Arial)
      - **Metric‑compatible** – similar metrics (e.g. Carlito → Calibri)
      - **Visual** – similar appearance, different metrics (e.g. Montserrat → Futura PT)
      - **Generic** – generic family fallback (e.g. sans‑serif → DejaVu Sans)
      - **Unsafe** – high‑risk substitution (e.g. symbol fonts like Wingdings)

   Risk classification
      The danger level of a substitution:

      - **Low** – exact or metric‑compatible
      - **Medium** – visual fallback
      - **High** – unsafe substitutions (symbol fonts, CJK → Latin)
      - *Where shown* – in scan and resolution reports.

   dry‑run
      Test mode that shows what would be done **without executing** any actions.

      *Example*: ``pptx-font-resolver install-missing ./documents --provider google --dry-run``
      *Purpose*: Verify actions before performing them.

   GUI
      Qt graphical interface (PySide6) for scanning, resolving, and installing fonts.

      *Launch*: ``pptx-font-resolver-gui``
      *Features*: Scan view, resolution view, install actions, export, fallback management.

   provider
      The source used to resolve a missing font:

      - ``fontist`` – install via Fontist
      - ``apt`` – install via Debian/Ubuntu packages
      - ``google`` – install via Google Fonts
      - ``local`` – local Fontconfig status
      - ``all`` – combine all sources

      *Command*: ``pptx-font-resolver resolve ./documents --provider google``

   ignore (session‑only)
      GUI action that hides a font **only for the current session**.

      *Difference*: Unlike ``accept‑fallback`` it does **not** create a persistent rule.
      *Use case*: Temporarily suppress a font you have already handled.

   license acceptance
      Explicit confirmation required to install certain fonts via Fontist.

      *Command*: ``--accept-license`` (CLI) or the GUI confirmation dialog.
      *Why?* – to respect font licensing.

   ZIP safety guard
      Size limit that prevents scanning pathological archives.

      *Threshold*: 500 MiB (524 288 000 bytes)
      *Example*: ``archive uncompressed size exceeds limit: 1498762844 > 524288000``

