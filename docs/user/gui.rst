Qt GUI
======

Lancez l'interface graphique avec :

.. code-block:: bash

   pptx-font-resolver-gui

L'interface réutilise le même moteur d'analyse que la CLI. Elle fournit une interface visuelle pour scanner, reviewer et résoudre les problèmes de polices.

.. contents::
   :local:

.. _gui-scan-view:

Scan View
--------

La vue par défaut permet de scanner un dossier et d'afficher les polices utilisées.

Éléments de l'interface :

+---------------------+--------------------------------------------------+
| Élément             | Description                                    |
+=====================+==================================================+
| **Barre de menu**   | Fichier, Édition, Affichage, Aide              |
+---------------------+--------------------------------------------------+
| **Barre d'outils** | Boutons rapides : Scan, Stop, Exporter           |
+---------------------+--------------------------------------------------+
| **Sélecteur de dossier** | Bouton pour choisir un dossier à scanner       |
+---------------------+--------------------------------------------------+
| **Profondeur**      | Menu déroulant (1, 2, infinite)                |
+---------------------+--------------------------------------------------+
| **Nombre de jobs**  | Menu déroulant (1 à 8)                         |
+---------------------+--------------------------------------------------+
| **Filtrer aux manquantes** | Case à cocher pour afficher uniquement les polices manquantes |
+---------------------+--------------------------------------------------+
| **Tableau**         | Affiche les polices, leur statut, occurrences, fichiers |
+---------------------+--------------------------------------------------+
| **Panneau de détails** | Affiche les informations détaillées pour la ligne sélectionnée |
+---------------------+--------------------------------------------------+

Résultats attendus :


- **Vert** : Police installée exactement
- **Rouge** : Police non disponible via Fontist
- **Jaune** : Installation échouée
- **Gris** : Ignorée (session-only)

.. note::
   Double-cliquez sur une ligne pour voir les détails dans le panneau de droite.

.. _gui-resolution-view:

Resolution View
---------------

Passez à l'onglet **Résolution** pour voir les recommandations de résolution multi-sources.

Colonnes affichées :

+---------------------+--------------------------------------------------+
| Colonne             | Description                                    |
+=====================+==================================================+
| **Install**         | Case à cocher pour sélectionner une police        |
+---------------------+--------------------------------------------------+
| **Family**          | Nom de la famille de police                    |
+---------------------+--------------------------------------------------+
| **Installed**       | ✅ si la police est installée exactement         |
+---------------------+--------------------------------------------------+
| **Fontist**         | ✅ si la police est disponible via Fontist      |
+---------------------+--------------------------------------------------+
| **Recommended action** | Action recommandée (Install via Fontist, Accept fallback, etc.) |
+---------------------+--------------------------------------------------+
| **Recommended family** | Famille suggérée pour substitution              |
+---------------------+--------------------------------------------------+
| **Relation**        | Type de relation (exact, metric-compatible, visual) |
+---------------------+--------------------------------------------------+
| **Risk**           | Niveau de risque (Low, Medium, High)           |
+---------------------+--------------------------------------------------+
| **Source**          | Source de la recommandation (fontist, google, local) |
+---------------------+--------------------------------------------------+
| **Files**           | Liste des fichiers utilisant cette police         |
+---------------------+--------------------------------------------------+

Actions disponibles (boutons en haut) :

+-------------------------------------+--------------------------------------+
| Bouton                             | Action                               |
+=====================================+======================================+
| **Install via Fontist**             | Installer la police via Fontist       |
+-------------------------------------+--------------------------------------+
| **Install via Google Fonts**        | Installer via Google Fonts            |
+-------------------------------------+--------------------------------------+
| **Install system package**            | Installer via apt                    |
+-------------------------------------+--------------------------------------+
| **Install safe recommendations**    | Installer toutes les recommandations sûres |
+-------------------------------------+--------------------------------------+
| **Import font file**                | Importer une police utilisateur        |
+-------------------------------------+--------------------------------------+
| **Accept fallback**                 | Créer un alias Fontconfig             |
+-------------------------------------+--------------------------------------+
| **Ignore**                         | Ignorer la police (session-only)       |
+-------------------------------------+--------------------------------------+
| **Exporter**                       | Exporter le tableau (JSON, CSV, Markdown) |
+-------------------------------------+--------------------------------------+

.. note::
   - Le bouton **Install safe recommendations** installe toutes les polices marquées comme sûres (Low/Medium risk).
   - Les boutons d'action sont désactivés si aucune ligne n'est sélectionnée.

Couleurs après installation
--------------------------

Après une installation réussie, les lignes deviennent **vertes** et affichent :


.. code-block:: text

   ✅ Installed via Fontist
   ✅ Installed via Google Fonts
   ✅ Imported

Si une installation échoue, la ligne devient **jaune** avec un message d'erreur dans le panneau de détails.

Panneau de détails
-----------------

Le panneau de droite affiche des informations détaillées pour la ligne sélectionnée :

- **Statut** : Installed/Not installed/Substituted
- **Occurrences** : Nombre de fois où la police est utilisée
- **Fichiers** : Liste des fichiers utilisant cette police
- **Recommandation** : Détail de l'action recommandée
- **Alias Fontconfig** : Si un fallback est actif
- **Logs** : Messages de log (erreurs, avertissements)

Exemple de détails :

.. code-block:: text

   Family: Futura PT Bold
   Status: Not installed
   Occurrences: 5
   Files: pres1.pptx, pres2.pptx
   Recommendation: Accept fallback to Montserrat (visual)
   Alias Fontconfig: Futura PT Bold → Montserrat
   Logs: Alias created successfully

Export
------

Les deux vues (Scan et Résolution) supportent l'export dans plusieurs formats :

- **JSON** : Données brutes pour traitement automatisé
- **CSV** : Tableau lisible dans un tableur
- **Markdown** : Rapport lisible en texte

Pour exporter :

1. Cliquez sur le bouton **Exporter** (en haut à droite)
2. Choisissez le format
3. Choisissez un emplacement pour sauvegarder le fichier
4. Cliquez sur **Enregistrer**

Exemple de rapport Markdown exporté :

.. code-block:: markdown

   # Rapport de scan - 24/06/2026

   ## Résumé
   - Dossier: ~/Documents/Présentations
   - Polices uniques: 42
   - Polices manquantes: 12

   ## Polices

   | Family         | Status      | Occurrences | Files                     |
   |----------------|-------------|-------------|---------------------------|
   | Calibri        | Missing     | 42         | pres1.pptx, pres2.pptx   |
   | Aptos          | Missing     | 12         | rapport.docx              |
   | Montserrat      | Installed   | 8          | pres1.pptx                |
   | Futura PT Bold  | Substituted | 5          | pres3.pptx                |

.. _gui-workers:

Workers et gestion des tâches
-----------------------------

L'interface utilise des workers en arrière-plan pour :

- Scanner les dossiers
- Installer des polices
- Résoudre les recommandations

Gestion des workers :

- **Lancement** : Automatique lors du scan ou de l'installation
- **Arrêt** : Les workers sont arrêtés automatiquement lors de la fermeture de la fenêtre
- **Affichage** : Une barre de progression montre l'état du worker en cours

.. note::
   Fermer la fenêtre pendant un scan ou une installation peut causer des erreurs. Laissez les tâches se terminer avant de fermer.

Mode offscreen (pour tests CI)
---------------------------

L'interface peut être lancée sans interface graphique pour des tests automatisés :

.. code-block:: bash

   env QT_QPA_PLATFORM=offscreen \
       pptx-font-resolver-gui

Résultat attendu :

- La fenêtre est créée en arrière-plan
- ``window.windowTitle()`` retourne le titre de la fenêtre
- La fenêtre est fermée automatiquement
- Code de sortie : 0 (succès)

.. note::
   Utile pour valider que l'interface se lance correctement dans un pipeline CI/CD.

Astuces
-------

- **Tri** : Cliquez sur l'en-tête d'une colonne pour trier le tableau
- **Recherche** : Utilisez la barre de recherche en haut à droite pour filtrer les polices
- **Sélection multiple** : Maintenez Ctrl/Cmd pour sélectionner plusieurs lignes
- **Re-scan** : Bouton **Re-scan** pour relancer une analyse après installation

Voir aussi
-------

- :doc:`gui-cas-pratiques` pour des cas d'usage concrets
- :doc:`fallbacks` pour comprendre les alias Fontconfig
- :doc:`resolve-workflow` pour un workflow complet
