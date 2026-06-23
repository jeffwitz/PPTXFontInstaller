Contributing
===========

Merci de votre intérêt pour contribuer à ``pptx-font-resolver`` !
Cette page explique comment **mettre en place un environnement de développement**, **suivre les conventions du projet**, et **soumettre des modifications**.

.. contents::
   :local:

.. _dev-setup:

Mise en place de l'environnement
-------------------------------

1. **Cloner le dépôt** (si ce n'est pas déjà fait) :

   .. code-block:: bash

      git clone https://github.com/<votre-utilisateur>/PPTXFontInstaller.git
      cd PPTXFontInstaller

2. **Créer un environnement virtuel** :

   .. code-block:: bash

      python -m venv .venv
      source .venv/bin/activate

3. **Installer le package en mode développement** :

   .. code-block:: bash

      pip install -e ".[dev,gui,font-import]"

   .. note::
      - ``dev`` installe ``pytest`` et ``ruff`` pour les tests et le linting
      - ``gui`` installe ``PySide6`` pour l'interface Qt
      - ``font-import`` installe ``fonttools`` pour lire les métadonnées des polices

4. **Vérifier l'installation** :

   .. code-block:: bash

      pptx-font-resolver --help
      pptx-font-resolver-gui --help
      pytest --version
      ruff --version

Validation avant commit
----------------------

Avant de soumettre une modification, exécutez ces commandes pour valider votre travail :

.. code-block:: bash

   # 1. Linting (pas d'erreurs)
   ruff check .

   # 2. Tests (102 tests doivent passer)
   pytest -q

   # 3. Compilation des modules Python (pas d'erreurs)
   python -m compileall pptx_font_resolver tests

   # 4. Build de la documentation (pas d'erreurs)
   sphinx-build -b html docs docs/_build/html

.. note::
   - ``ruff check .`` doit retourner **0** problème
   - ``pytest -q`` doit retourner **102 passed**
   - ``compileall`` ne doit pas afficher d'erreur
   - ``sphinx-build`` ne doit pas afficher d'erreur ou d'avertissement critique

Conventions de code
-----------------

1. **Nommage** :
   - Modules : ``snake_case.py`` (ex: ``fontconfig.py``)
   - Classes : ``PascalCase`` (ex: ``FontScanner``)
   - Fonctions : ``snake_case()`` (ex: ``scan_folder()``)
   - Variables : ``snake_case`` (ex: ``font_family``)

2. **Docstrings** :
   - Format **Google** ou **NumPy**
   - Exemple Google :
     
     .. code-block:: python
     
        def scan_folder(path: str, depth: int, jobs: int) -> list[FileEntry]:
            """Scan a folder for Office files.

            Args:
                path: The folder to scan.
                depth: Recursion depth (integer or "infinite").
                jobs: Number of parallel workers.

            Returns:
                A list of scanned file entries.
            """
   - Exemple NumPy :
     
     .. code-block:: python
     
        def resolve_font(family: str) -> FontResolution:
            '''Resolve a font family to a recommended action.

            Parameters
            ----------
            family : str
                The font family name to resolve.

            Returns
            -------
            FontResolution
                The resolution object with recommended action.
            '''

3. **Typage** :
   - Utilisez les types Python natifs et ``typing``
   - Exemple : ``def scan_folder(path: str, depth: int | str) -> list[FileEntry]:``

4. **Gestion des erreurs** :
   - Utilisez des exceptions spécifiques (``ValueError``, ``FileNotFoundError``)
   - Ne capturez pas ``Exception`` sauf si nécessaire
   - Loggez les erreurs avec ``logging``

5. **Imports** :
   - Regroupez les imports par catégorie :
     
     .. code-block:: python
     
        # Standard library
        import os
        import zipfile

        # Third-party
        from typer import Typer
        from rich.console import Console

        # Local application
        from pptx_font_resolver.models import FileEntry

.. _tests-guidelines:

Lignes directrices pour les tests
-------------------------------

1. **Couverture** :
   - Tous les modules doivent avoir des tests
   - Les tests critiques : ``scanner``, ``resolution/engine``, ``fontconfig``, ``qt_app``
   - Objectif : **100% des fonctions publiques testées**

2. **Structure des tests** :
   - Fichiers : ``test_<module>.py`` dans ``tests/``
   - Exemple : ``tests/test_scanner.py`` pour ``pptx_font_resolver/scanner.py``
   - Utilisez ``pytest`` et ``pytest.mark.parametrize`` pour les cas multiples

3. **Fixtures** :
   - Utilisez ``conftest.py`` pour les fixtures partagées
   - Exemple : ``tmp_font_dir`` pour un dossier temporaire de polices

4. **Cas de test** :
   - Cas normaux : Fichiers valides, polices installées
   - Cas limites : Fichiers corrompus, polices manquantes, substitutions
   - Cas d'erreur : Exceptions, timeouts, permissions

5. **Tests GUI** :
   - Utilisez ``QT_QPA_PLATFORM=offscreen`` pour tester sans interface graphique
   - Exemple : ``tests/test_qt_app.py``

Exemple de test
~~~~~~~~~~~~

.. code-block:: python

   def test_scan_folder(tmp_path):
       """Test that scan_folder discovers .pptx and .docx files."""
       # Créer des fichiers de test
       (tmp_path / "pres.pptx").touch()
       (tmp_path / "doc.docx").touch()
       
       # Exécuter
       results = scan_folder(str(tmp_path), depth=1, jobs=1)
       
       # Vérifier
       assert len(results) == 2
       assert any(r.path.endswith("pres.pptx") for r in results)
       assert any(r.path.endswith("doc.docx") for r in results)

.. _commit-guidelines:

Lignes directrices pour les commits
-------------------------------

1. **Message de commit** :
   - Format : ``[type] Description``
   - Exemples :
     
     .. code-block:: text
     
        [feat] Ajouter support des polices CJK
        
        - pptx_font_resolver/fontconfig.py: normaliser "Noto Sans CJK SC Regular"
        - tests/test_fontconfig.py: ajouter cas CJK
        - docs/user/troubleshooting.rst: ajouter section CJK
        
        Closes #123

        [fix] Corriger crash lors du scan de fichiers corrompus
        
        - pptx_font_resolver/scanner.py: ajouter guard contre fichiers ZIP invalides
        - tests/test_scanner.py: ajouter cas de fichier corrompu
        
        Fixes #456

   - Types de commit :
     
     - ``[feat]`` : Nouvelle fonctionnalité
     - ``[fix]`` : Correction de bug
     - ``[docs]`` : Mise à jour de la documentation
     - ``[test]`` : Ajout ou mise à jour de tests
     - ``[refactor]`` : Refactoring sans changement de comportement
     - ``[chore]`` : Maintenance (CI, dépendances, etc.)

2. **Scope** :
   - Un commit = une modification cohérente
   - Évitez les commits "fourre-tout" avec plusieurs changements non liés

3. **Branches** :
   - Développez directement sur ``main``
   - ``git commit && git push origin main`` après validation

.. _pr-guidelines:

Lignes directrices pour les Pull Requests
------------------------------------

1. **Titre** :
   - Suivez le format des commits : ``[type] Description``
   - Exemple : ``[feat] Ajouter CLI pour lister les fallbacks``

2. **Description** :
   - Expliquez **pourquoi** le changement est nécessaire
   - Listez les **changements** effectués
   - Mentionnez les **issues** fermées (``Closes #123``)
   - Ajoutez des **captures d'écran** si l'interface est modifiée

3. **Validation** :
   - La PR doit passer tous les tests CI
   - La PR doit être reviewée par au moins un contributeur
   - La PR doit être **squash-merge** dans ``main``

Exemple de description de PR
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: markdown

   Ajoute le CLI pour gérer les fallbacks Fontconfig
   
   **Pourquoi** : Les utilisateurs veulent lister/supprimer les alias sans éditer manuellement les fichiers.
   
   **Changements** :
   - Ajout de ``pptx-font-resolver list-fallbacks``
   - Ajout de ``pptx-font-resolver remove-fallback <family>``
   - Mise à jour de ``docs/user/fallbacks.rst`` avec les nouvelles commandes
   
   **Validation** :
   - [x] ``ruff check .`` → 0 problèmes
   - [x] ``pytest -q`` → 102 passed
   - [x] ``sphinx-build`` → 0 erreurs
   
   **Issues** : Relates to #789

.. _publishing:

Publier une nouvelle version
--------------------------

1. **Mettre à jour la version** :

   .. code-block:: bash

      # Dans pyproject.toml
      version = "0.1.1"  # Incrémentez le patch ou le minor

2. **Construire le package** :

   .. code-block:: bash

      pip install hatch
      hatch build

3. **Publier sur PyPI** :

   .. code-block:: bash

      hatch publish

4. **Créer un tag Git** :

   .. code-block:: bash

      git tag v0.1.1
      git push origin v0.1.1

5. **Mettre à jour le CHANGELOG** :

   .. code-block:: bash

      # Ajoutez une entrée dans CHANGELOG.md
      ## [0.1.1] - 2026-06-24
      
      ### Ajouté
      - CLI ``list-fallbacks`` et ``remove-fallback``
      
      ### Corrigé
      - Crash lors du scan de fichiers ZIP corrompus

.. _resources:

Ressources utiles
---------------

- **Documentation officielle** : https://pptx-font-resolver.readthedocs.io/
- **Dépôt GitHub** : https://github.com/jeffwitz/PPTXFontInstaller
- **Issues** : https://github.com/jeffwitz/PPTXFontInstaller/issues
- **Discussions** : https://github.com/jeffwitz/PPTXFontInstaller/discussions

- **Sphinx** : https://www.sphinx-doc.org/
- **RTD Theme** : https://sphinx-rtd-theme.readthedocs.io/
- **Typer** : https://typer.tiangolo.com/
- **PySide6** : https://doc.qt.io/qtforpython/


.. _faq-dev:

FAQ Développeur
--------------

**Comment déboguer un test qui échoue ?**

.. code-block:: bash

   pytest -xvs tests/test_scanner.py::test_scan_folder

**Comment tester la GUI sans interface graphique ?**

.. code-block:: bash

   env QT_QPA_PLATFORM=offscreen pytest -xvs tests/test_qt_app.py

**Comment ajouter une nouvelle dépendance ?**

1. Ajoutez-la dans ``pyproject.toml`` sous la section appropriée (``dev``, ``gui``, ``font-import``)
2. Exécutez ``pip install -e ".[dev,gui,font-import]"`` pour la tester
3. Mettez à jour ``docs/conf.py`` si la dépendance est utilisée dans la documentation
4. Ajoutez des tests pour la nouvelle fonctionnalité
5. Soumettez une PR

**Comment contribuer à la documentation ?**

- Modifiez les fichiers ``.rst`` dans ``docs/user/`` ou ``docs/api/``
- Exécutez ``sphinx-build -b html docs docs/_build/html`` pour valider
- Soumettez une PR avec le préfixe ``[docs]``

Résumé des commandes utiles
--------------------------

+-------------------------------------+--------------------------------------+
| Objectif                            | Commande                             |
+=====================================+======================================+
| Installer en dev                    | pip install -e ".[dev,gui,font-import]" |
+-------------------------------------+--------------------------------------+
| Lancer les tests                    | pytest -q                           |
+-------------------------------------+--------------------------------------+
| Lancer le linting                  | ruff check .                        |
+-------------------------------------+--------------------------------------+
| Build la documentation             | sphinx-build -b html docs docs/_build/html |
+-------------------------------------+--------------------------------------+
| Tester la GUI (offscreen)          | env QT_QPA_PLATFORM=offscreen pptx-font-resolver-gui |
+-------------------------------------+--------------------------------------+
| Vérifier les imports                | python -m compileall pptx_font_resolver tests |
+-------------------------------------+--------------------------------------+

Si vous avez des questions, ouvrez une **discussion** sur GitHub ou contactez le mainteneur.
