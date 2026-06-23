Cas pratiques avec l'interface GUI
==================================

Cette page montre **comment utiliser l'interface graphique** pour résoudre des problèmes concrets de polices manquantes.

.. contents::
   :local:

Cas 1 : Installer toutes les polices manquantes via Google Fonts
---------------------------------------------------------------

**Scénario** : Vous avez 15 polices manquantes, toutes disponibles via Google Fonts.

**Étapes** :

1. Lancez l'interface :
   
   .. code-block:: bash
   
      pptx-font-resolver-gui

2. Cliquez sur **Choisir un dossier** et sélectionnez votre dossier de documents

3. Cochez **Filtrer aux polices manquantes** (en haut à droite)

4. Passez à l'onglet **Résolution**

5. Cliquez sur **Installer via Google Fonts** (bouton en haut)

6. Une popup apparaît avec une liste de polices et des boutons :
   
   - **Oui** : Installer cette police
   - **Oui pour toutes** : Installer toutes les polices de la liste
   - **Non** : Ignorer cette police

7. Cliquez sur **Oui pour toutes**

8. La scan se relance automatiquement

9. Les lignes des polices installées deviennent **vertes**

Résultat attendu :

- Toutes les polices manquantes sont installées
- Les lignes sont vertes avec ✅ dans la colonne "Installed"
- Un message en bas confirme le nombre de polices installées

Astuce :
- Si une police est en **rouge**, elle n'est pas disponible via Google Fonts → utilisez ``import-font`` ou ``accept-fallback``
- Si une police est en **jaune**, l'installation a échoué → vérifiez les logs

Cas 2 : Accepter un fallback pour une police symbolique
---------------------------------------------------

**Scénario** : Vous avez ``Wingdings`` dans un document et voulez éviter les boîtes ou symboles incorrects.

**Étapes** :

1. Dans l'onglet **Résolution**, trouvez la ligne avec ``Wingdings``
2. Colonne **Risk** : ⚠️ **High**
3. Colonne **Recommended action** : ``Accept fallback``
4. Cliquez sur **Explain** pour voir les détails
5. Cliquez sur **Accept fallback**
6. Une popup apparaît avec :
   
   .. code-block:: text
   
      Créer un alias Fontconfig :
      Wingdings → Noto Sans Symbols
      
      ⚠️ Attention : Cette substitution peut changer le sens des glyphes.
      Voulez-vous continuer ?
      
      [Oui] [Non]

7. Cliquez sur **Oui**

8. La ligne devient **verte** et affiche :
   
   .. code-block:: text
   
      Alias créé : Wingdings → Noto Sans Symbols
      Fichier : ~/.config/fontconfig/conf.d/90-pptx-font-resolver.conf

9. Vérifiez dans le panneau de détails :
   
   .. code-block:: text
   
      Alias Fontconfig : Wingdings → Noto Sans Symbols

10. Rafraîchissez LibreOffice pour voir le rendu

Résultat attendu :

- Les symboles ``Wingdings`` sont rendus avec ``Noto Sans Symbols``
- Le document PowerPoint n'est pas modifié
- La règle est persistante (reste après redémarrage)

Cas 3 : Installer une police spécifique via Fontist
-----------------------------------------------

**Scénario** : Vous voulez installer ``Aptos`` via Fontist (si disponible).


**Étapes** :

1. Dans l'onglet **Résolution**, trouvez la ligne avec ``Aptos``
2. Colonne **Fontist** : ✅ **Available**
3. Colonne **Recommended action** : ``Install via Fontist``
4. Cliquez sur **Install via Fontist**
5. Une popup apparaît avec :
   
   .. code-block:: text
   
      Installer Aptos via Fontist ?
      
      ⚠️ Licence : Apache 2.0
      Voulez-vous accepter la licence et installer ?
      
      [Oui] [Non]

6. Cliquez sur **Oui**
7. L'installation se lance en arrière-plan
8. Une notification apparaît : "Aptos installé avec succès"
9. La ligne devient **verte** avec ✅ dans la colonne "Installed"

Résultat attendu :

- ``Aptos`` est installé dans ``~/.local/share/fonts/``
- ``fc-match "Aptos"`` retourne ``Aptos``
- La police est disponible pour tous les logiciels (LibreOffice, OnlyOffice, etc.)

Cas 4 : Exporter un rapport pour un collègue
------------------------------------------

**Scénario** : Vous voulez partager un rapport de scan avec votre équipe.

**Étapes** :

1. Cliquez sur l'onglet **Scan** ou **Résolution**
2. Cliquez sur **Exporter** (bouton en haut à droite)
3. Choisissez le format : JSON, CSV ou Markdown
4. Choisissez un emplacement pour sauvegarder le fichier
5. Envoyez le fichier à votre collègue

Exemple de rapport Markdown exporté :

.. code-block:: markdown

   # Rapport de résolution - 24/06/2026

   ## Résumé
   - Dossier : ~/Documents/Présentations
   - Polices manquantes : 12
   - Polices installées : 8

   ## Détails

   | Family         | Installed | Fontist | Recommended action | Relation      |
   |----------------|-----------|---------|-------------------|---------------|
   | Calibri        | ❌       | ✅      | Install via Fontist | exact         |
   | Aptos          | ❌       | ❌      | Install via Google Fonts | visual      |
   | Futura PT Bold  | ❌       | ❌      | Accept fallback    | visual        |

   ## Actions recommandées
   - Installer Calibri via Fontist
   - Installer Aptos via Google Fonts
   - Accepter le fallback pour Futura PT Bold

Cas 5 : Ignorer une police temporairement
---------------------------------------

**Scénario** : Vous avez une police ``LegacySans-Bold`` qui est en rouge (non disponible) mais vous ne voulez pas la traiter maintenant.

**Étapes** :

1. Dans l'onglet **Résolution**, trouvez la ligne avec ``LegacySans-Bold``
2. Colonne **Recommended action** : ``Ignore``
3. Cliquez sur **Ignore**
4. La ligne devient **grise** et reste visible

Résultat attendu :

- La ligne est masquée dans la session en cours
- Elle réapparaît si vous relancez le scan
- Contrairement à ``accept-fallback``, elle n'est pas persistante

Cas 6 : Importer une police utilisateur
-------------------------------------

**Scénario** : Vous avez ``~/Downloads/FuturaPT.ttf`` et le droit de l'utiliser.

**Étapes** :

1. Cliquez sur l'onglet **Résolution**
2. Cliquez sur **Import font file** (bouton en haut)
3. Une fenêtre de fichier s'ouvre → sélectionnez ``~/Downloads/FuturaPT.ttf``
4. Choisissez **Copier** ou **Créer un lien symbolique**
5. Cliquez sur **Importer**
6. Une notification apparaît : "FuturaPT importée avec succès"
7. Rafraîchissez le scan (bouton **Re-scan**)
8. La ligne devient **verte** avec ✅ dans la colonne "Installed"

Résultat attendu :

- ``FuturaPT`` est installé dans ``~/.local/share/fonts/pptx-font-installer/imported/``
- ``fc-match "Futura PT Bold"`` retourne ``FuturaPT``
- La police est disponible pour tous les logiciels

Cas 7 : Résoudre une police CJK
--------------------------------

**Scénario** : Vous avez ``Noto Sans CJK SC Regular`` qui est substitué par ``Noto Sans`` (risque élevé).


**Étapes** :

1. Dans l'onglet **Résolution**, trouvez la ligne avec ``Noto Sans CJK SC Regular``
2. Colonne **Risk** : ⚠️ **High** (CJK → Latin)
3. Colonne **Recommended action** : ``Install system package`` ou ``Import font file``
4. Cliquez sur **Explain** pour voir les détails
5. Installez la police CJK exacte via le gestionnaire de paquets :
   
   .. code-block:: bash
   
      sudo apt install fonts-noto-cjk
   
6. Ou importez la police si vous avez le fichier ``.ttf``
7. Rafraîchissez le scan
8. La ligne devient **verte**

Résultat attendu :

- Les caractères CJK sont correctement rendus
- Pas de perte de données

Cas 8 : Utiliser l'interface en mode offscreen (CI/CD)
------------------------------------------------------

**Scénario** : Vous voulez tester l'interface sans interface graphique (pour des tests automatisés).

**Commande** :

.. code-block:: bash

   env QT_QPA_PLATFORM=offscreen \
       pptx-font-resolver-gui

Résultat attendu :

- L'interface se lance en arrière-plan
- ``window.windowTitle()`` retourne le titre de la fenêtre
- La fenêtre est fermée automatiquement
- Code de sortie : 0 (succès)

Boutons et actions par onglet
-----------------------------

Onglet **Scan**
~~~~~~~~~~~~

+---------------------+--------------------------------------------------+
| Élément             | Action                                         |
+=====================+==================================================+
| Dossier             | Sélectionner un dossier à scanner                |
+---------------------+--------------------------------------------------+
| Profondeur          | Choisir une profondeur (1, 2, infinite)         |
+---------------------+--------------------------------------------------+
| Nombre de jobs      | Choisir le nombre de workers parallèles          |
+---------------------+--------------------------------------------------+
| Filtrer aux manquantes | Cocher pour afficher uniquement les polices manquantes |
+---------------------+--------------------------------------------------+
| Lancer le scan      | Bouton **Scan**                                |
+---------------------+--------------------------------------------------+
| Arrêter le scan     | Bouton **Stop** (si le scan est en cours)      |
+---------------------+--------------------------------------------------+
| Exporter            | Bouton **Exporter** (JSON, CSV, Markdown)       |
+---------------------+--------------------------------------------------+

Onglet **Résolution**
~~~~~~~~~~~~~~~~~~

+---------------------+--------------------------------------------------+
| Élément             | Action                                         |
+=====================+==================================================+
| Installer via Fontist | Bouton **Install via Fontist** (par ligne)     |
+---------------------+--------------------------------------------------+
| Installer via Google Fonts | Bouton **Install via Google Fonts** (par ligne) |
+---------------------+--------------------------------------------------+
| Installer système   | Bouton **Install system package** (par ligne)    |
+---------------------+--------------------------------------------------+
| Installer recommandations | Bouton **Install safe recommendations** (toutes) |
+---------------------+--------------------------------------------------+
| Importer une police | Bouton **Import font file** (par ligne)         |
+---------------------+--------------------------------------------------+
| Accepter fallback   | Bouton **Accept fallback** (par ligne)          |
+---------------------+--------------------------------------------------+
| Ignorer             | Bouton **Ignore** (par ligne)                   |
+---------------------+--------------------------------------------------+
| Exporter            | Bouton **Exporter** (JSON, CSV, Markdown)       |
+---------------------+--------------------------------------------------+

Astuces
-------

- **Double-cliquez** sur une ligne pour voir les détails dans le panneau de droite
- **Tri par colonne** : Cliquez sur l'en-tête d'une colonne pour trier
- **Recherche** : Utilisez la barre de recherche en haut à droite
- **Rafraîchir** : Bouton **Re-scan** pour relancer une analyse après installation

Résumé des couleurs
------------------

+--------+-------------------------------+-------------------------------+
| Couleur | Signification                 | Action recommandée             |
+========+===============================+===============================+
| Vert   | Police installée ou fallback créé | Aucune                       |
+--------+-------------------------------+-------------------------------+
| Rouge  | Police non disponible via Fontist | Utilisez ``import-font`` ou ``accept-fallback`` |
+--------+-------------------------------+-------------------------------+
| Jaune  | Installation échouée           | Vérifiez les logs            |
+--------+-------------------------------+-------------------------------+
| Gris   | Ignorée (session-only)         | Cliquez sur **Ignore** pour la réactiver |
+--------+-------------------------------+-------------------------------+
