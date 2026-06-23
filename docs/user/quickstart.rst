Quickstart
==========

Vous avez des problèmes de polices manquantes dans vos fichiers PowerPoint ou Word sous Linux ?
Ce guide vous fait démarrer en **3 étapes**.

.. contents::
   :local:

Étape 1 — Installer
-------------------

Installez le package avec les dépendances GUI (interface graphique) :

.. code-block:: bash

   # Dans le dépôt PPTXFontInstaller
   pip install -e ".[dev,gui]"

   # Vérifiez l'installation
   pptx-font-resolver --help
   pptx-font-resolver-gui --help

.. note::
   - ``dev`` installe ``pytest`` et ``ruff`` pour les tests et le linting.
   - ``gui`` installe ``PySide6`` pour l'interface Qt.
   - Si vous n'avez pas besoin de l'interface, utilisez ``pip install -e ".[dev,font-import]"``.

Étape 2 — Scanner vos documents
-------------------------------

Scannez un dossier contenant vos fichiers PowerPoint (``.pptx``) ou Word (``.docx``) :


.. code-block:: bash

   # Scannez un dossier (profondeur infinie)
   pptx-font-resolver scan ~/Documents/Présentations --depth infinite

   # Listez toutes les polices trouvées
   pptx-font-resolver fonts ~/Documents/Présentations --all-fonts --show-files

Résultat attendu :

.. code-block:: text

   Family         | Status      | Occurrences | Files
   ---------------+-------------+------------+--------------------------------------
   Calibri        | Missing     | 42         | pres1.pptx, pres2.pptx
   Aptos          | Missing     | 12         | rapport.docx
   Montserrat      | Installed   | 8          | pres1.pptx
   Futura PT Bold  | Substituted | 5          | pres3.pptx

Étape 3 — Résoudre les polices manquantes
---------------------------------------

Générez un rapport de résolution pour voir les options disponibles :

.. code-block:: bash

   # Résolution multi-sources (Fontist, Google Fonts, paquets apt)
   pptx-font-resolver resolve ~/Documents/Présentations --provider all --format table

Résultat attendu :

.. code-block:: text

   Family         | Installed | Fontist | Recommended action       | Relation
   ---------------+-----------+---------+------------------------+--------------
   Calibri        | ❌       | ✅      | Install via Fontist    | exact
   Aptos          | ❌       | ❌      | Install via Google Fonts | visual
   Futura PT Bold  | ❌       | ❌      | Accept fallback        | visual

Installez les polices via Google Fonts (exemple) :

.. code-block:: bash

   # Aperçu des installations (sans téléchargement)
   pptx-font-resolver install-missing ~/Documents/Présentations \
       --provider google --dry-run

   # Exécutez les installations
   pptx-font-resolver install-missing ~/Documents/Présentations \
       --provider google --execute --yes

Acceptez un fallback pour une police manquante (exemple) :

.. code-block:: bash

   pptx-font-resolver accept-fallback "Futura PT Bold" "Montserrat"

   # Vérifiez que l'alias est actif
   fc-match "Futura PT Bold"

Résultat attendu :

.. code-block:: text

   Montserrat: "Montserrat:style=Regular"

.. note::
   - Les polices installées via Google Fonts sont placées dans :
     ``~/.local/share/fonts/pptx-font-installer/google-fonts/``
   - Les alias Fontconfig sont écrits dans :
     ``~/.config/fontconfig/conf.d/90-pptx-font-resolver.conf``
   - Après toute installation, exécutez ``fc-cache -f`` pour rafraîchir le cache.

Cas d'usage courants
-------------------

**Vous voulez juste voir quelles polices sont utilisées ?**

.. code-block:: bash

   pptx-font-resolver fonts ./documents --format json --output fonts.json

**Vous voulez une liste des polices manquantes ?**

.. code-block:: bash

   pptx-font-resolver resolve ./documents --provider all --format markdown \
       | grep "❌ Missing"

**Vous voulez utiliser l'interface graphique ?**

.. code-block:: bash

   pptx-font-resolver-gui

   # Ou en mode offscreen (pour les tests CI)
   env QT_QPA_PLATFORM=offscreen pptx-font-resolver-gui

Prochaines étapes
---------------

- **GUI** : Consultez :doc:`gui` pour une visite guidée de l'interface.
- **Fallbacks** : Consultez :doc:`fallbacks` pour comprendre et gérer les alias Fontconfig.
- **Résolution avancée** : Consultez :doc:`resolve-workflow` pour un workflow complet.
- **Dépannage** : Consultez :doc:`troubleshooting` si un problème survient.

Exemple complet
---------------

Voici un exemple complet pour un dossier de présentations :

.. code-block:: bash

   # 1. Installer
   pip install -e ".[dev,gui]"

   # 2. Scanner
   pptx-font-resolver scan ~/CNRS/Presentations --depth infinite

   # 3. Résoudre via Google Fonts
   pptx-font-resolver resolve ~/CNRS/Presentations --provider google --format table
   pptx-font-resolver install-missing ~/CNRS/Presentations --provider google --execute --yes

   # 4. Accepter les fallbacks restants
   pptx-font-resolver accept-fallback "Futura PT Bold" "Montserrat"
   pptx-font-resolver accept-fallback "ElsevierGulliver" "Source Serif 4"

   # 5. Vérifier
   pptx-font-resolver fonts ~/CNRS/Presentations --all-fonts

Résultat final : toutes les polices sont installées ou substituées.
