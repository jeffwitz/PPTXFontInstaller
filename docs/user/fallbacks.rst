Fontconfig Fallbacks
====================

Cette page explique **pourquoi**, **quand** et **comment** utiliser les alias Fontconfig pour résoudre les polices manquantes.

.. contents::
   :local:

Pourquoi utiliser un fallback ?
---------------------------

Les alias Fontconfig sont utiles dans ces cas :

1. **Police propriétaire**
   - Exemple : Futura PT, Aptos, ElsevierGulliver
   - Solution : Mapper vers une alternative open-source (Montserrat, Source Serif 4)

2. **Police embarquée en subset**
   - Exemple : ``AdvOT...`` (nom généré automatiquement par PowerPoint)
   - Solution : Mapper vers une police générique (Noto Sans)

3. **Police symbolique**
   - Exemple : Wingdings, Webdings, ZapfDingbats
   - Solution : Mapper vers une police open-source (Noto Sans Symbols)

4. **Compatibilité visuelle**
   - Exemple : Calibri → Carlito (metric-compatible)
   - Solution : Mapper pour une apparence cohérente

.. note::
   Les fallbacks **ne modifient pas** le fichier Office. Ils configurent uniquement le système de rendu local (LibreOffice, OnlyOffice).

Quand utiliser un fallback vs. une installation ?
-----------------------------------------------

+----------------+----------------+----------------+----------------+
| Méthode       | Modifie doc ? | Persistant ?   | Risque        |
+================+================+================+================+
| **Fallback**   | ❌ Non        | ✅ Oui        | ⚠️ Medium      |
+----------------+----------------+----------------+----------------+
| **Install**    | ❌ Non        | ✅ Oui        | ✅ Faible      |
+----------------+----------------+----------------+----------------+
| **Import**     | ❌ Non        | ✅ Oui        | ✅ Faible      |
+----------------+----------------+----------------+----------------+

**Choisissez un fallback si :**
- La police est propriétaire et vous n'avez pas le droit de l'installer
- Vous voulez éviter les problèmes de licence
- Vous préférez une solution locale (pas de téléchargement)

**Choisissez une installation si :**
- La police est open-source (Google Fonts, Fontist)
- Vous voulez une solution permanente et exacte
- Vous avez besoin de métriques précises (pas de changement de mise en page)

Exemple concret : Futura PT Bold → Montserrat
-------------------------------------------

1. **Détection**
   
   .. code-block:: bash
   
      pptx-font-resolver resolve ~/documents --provider all --format table
   
   Résultat :
   
   .. code-block:: text
   
      Family         | Installed | Recommended action | Relation
      ---------------+-----------+-------------------+----------
      Futura PT Bold  | ❌       | Accept fallback   | visual

2. **Création de l'alias**
   
   .. code-block:: bash
   
      pptx-font-resolver accept-fallback "Futura PT Bold" "Montserrat" \
          --source google-fonts
   
   Fichiers créés/modifiés :
   
   - ``~/.config/pptx-font-resolver/fontconfig-aliases.json`` (stockage JSON)
   - ``~/.config/fontconfig/conf.d/90-pptx-font-resolver.conf`` (règle Fontconfig)
   - Exécution de ``fc-cache -f`` pour rafraîchir le cache

3. **Vérification**
   
   .. code-block:: bash
   
      fc-match "Futura PT Bold"
   
   Résultat attendu :
   
   .. code-block:: text
   
      Montserrat: "Montserrat:style=Regular"

4. **Résultat dans LibreOffice**
   
   - Le document PowerPoint référence toujours ``Futura PT Bold``
   - LibreOffice utilise ``Montserrat`` pour le rendu
   - Si vous sauvegardez avec **embedding de polices**, LibreOffice peut embedder ``Montserrat``

Gestion avancée des fallbacks
------------------------------

.. note::
   Les commandes CLI suivantes sont **planifiées** mais pas encore implémentées :
   
   - ``pptx-font-resolver list-fallbacks``
   - ``pptx-font-resolver remove-fallback "Futura PT Bold"``
   - ``pptx-font-resolver clear-fallbacks``

   En attendant, utilisez l'interface GUI ou éditez manuellement les fichiers.

Dans l'interface GUI
-------------------

1. Passez à l'onglet **Résolution**
2. Sélectionnez une ligne avec une recommandation ``Accept fallback``
3. Cliquez sur **Accept fallback**
4. La ligne devient verte et un message confirme la création de l'alias
5. Le fichier de configuration est affiché dans le panneau de détails

Exemple de fichier de configuration généré
---------------------------------------

.. code-block:: xml
   <?xml version="1.0"?>
   <!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
   <fontconfig>
     <alias>
       <family>Futura PT Bold</family>
       <prefer>
         <family>Montserrat</family>
       </prefer>
     </alias>
     <alias>
       <family>ElsevierGulliver</family>
       <prefer>
         <family>Source Serif 4</family>
       </prefer>
     </alias>
   </fontconfig>

Risques et avertissements
--------------------------

⚠️ **Symbol fonts (Wingdings, Webdings, etc.)**
   - **Risque élevé** : Les glyphes peuvent changer de sens (ex: ⚠️ → ❌)
   - **Solution** : Évitez les fallbacks pour les polices symboliques, ou utilisez une police open-source comme Noto Sans Symbols

⚠️ **CJK fonts substituées par des polices Latin**
   - Exemple : ``Noto Sans CJK SC Regular`` → ``Noto Sans``
   - **Risque** : Perte des caractères CJK (chinois, japonais, coréen)
   - **Solution** : Installez la police CJK exacte ou utilisez une police CJK open-source

⚠️ **Visual fallbacks vs. metric-compatible**
   - ``visual`` : Changement possible de mise en page
   - ``metric-compatible`` : Moins de risques de changement
   - **Conseil** : Préférez ``metric-compatible`` quand disponible

Test sans modifier la configuration réelle
--------------------------------------

Pour tester un fallback sans toucher à votre configuration Fontconfig :

.. code-block:: bash

   env XDG_CONFIG_HOME=/tmp/pptx-font-resolver-test \
       pptx-font-resolver accept-fallback "Futura PT Bold" "Montserrat" \
       --source google-fonts --no-refresh-cache

Résultat :

- L'alias est écrit dans ``/tmp/pptx-font-resolver-test/fontconfig/conf.d/90-pptx-font-resolver.conf``
- ``fc-match`` ne le prend pas en compte (car ``XDG_CONFIG_HOME`` est modifié)
- Utile pour valider la syntaxe avant de l'appliquer en production

Vérification des fallbacks existants
----------------------------------

Listez tous les fallbacks configurés :

.. code-block:: bash

   cat ~/.config/fontconfig/conf.d/90-pptx-font-resolver.conf

Vérifiez qu'un fallback est actif :

.. code-block:: bash

   fc-match "Futura PT Bold"
   # Doit retourner : Montserrat

Annulation d'un fallback
----------------------

Pour supprimer un fallback :

1. Éditez manuellement le fichier :
   
   .. code-block:: bash
   
      nano ~/.config/fontconfig/conf.d/90-pptx-font-resolver.conf
   
2. Supprimez la règle ``<alias>`` correspondante
3. Rafraîchissez le cache :
   
   .. code-block:: bash
   
      fc-cache -f

4. Vérifiez :
   
   .. code-block:: bash
   
      fc-match "Futura PT Bold"
   
   # Doit retourner la police originale ou une substitution système

Quand utiliser ``accept-fallback`` vs. ``import-font`` ?
-------------------------------------------------------

+----------------+----------------+----------------+----------------+
| Critère        | accept-fallback | import-font    | install-font   |
+================+================+================+================+
| Police         | Propriétaire   | User-owned    | Open-source    |
+----------------+----------------+----------------+----------------+
| Installation   | Locale (alias) | Copie locale  | Téléchargement|
+----------------+----------------+----------------+----------------+
| Persistance    | ✅ Oui        | ✅ Oui        | ✅ Oui        |
+----------------+----------------+----------------+----------------+
| Risque         | ⚠️ Medium      | ✅ Faible      | ✅ Faible      |
+----------------+----------------+----------------+----------------+

**Exemple** :
- ``accept-fallback`` : Futura PT Bold → Montserrat (propriétaire → open-source)
- ``import-font`` : Importer ``~/Downloads/Aptos.ttf`` (si vous avez le fichier)
- ``install-font`` : Installer Aptos via Fontist (si disponible)

Cas pratiques
-------------

Cas 1 : Police propriétaire sans fichier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Vous avez un PowerPoint avec ``Futura PT Bold`` mais pas le fichier ``.ttf``.

.. code-block:: bash

   pptx-font-resolver resolve ~/documents --provider all --format table
   # Résultat : Recommended action = Accept fallback

   pptx-font-resolver accept-fallback "Futura PT Bold" "Montserrat"
   fc-match "Futura PT Bold"  # Vérifiez

Cas 2 : Police propriétaire avec fichier
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Vous avez ``~/Downloads/FuturaPT.ttf`` et le droit de l'utiliser.

.. code-block:: bash

   pip install -e ".[font-import]"
   pptx-font-resolver import-font ~/Downloads/FuturaPT.ttf
   fc-cache -f
   fc-match "Futura PT Bold"  # Doit retourner FuturaPT

Cas 3 : Police open-source disponible
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Vous voulez installer ``Aptos`` (disponible via Google Fonts).

.. code-block:: bash

   pptx-font-resolver install-google-font "Aptos"
   fc-cache -f
   fc-match "Aptos"  # Doit retourner Aptos

Résumé des commandes
-------------------

+-------------------------------+--------------------------------------+
| Objectif                      | Commande                             |
+===============================+======================================+
| Créer un fallback            | accept-fallback "From" "To"          |
+-------------------------------+--------------------------------------+
| Lister les fallbacks          | cat ~/.config/fontconfig/...         |
+-------------------------------+--------------------------------------+
| Vérifier un fallback          | fc-match "Family"                    |
+-------------------------------+--------------------------------------+
| Supprimer un fallback         | Édition manuelle + fc-cache -f       |
+-------------------------------+--------------------------------------+
| Tester sans config réelle     | XDG_CONFIG_HOME=/tmp/test ... --no-refresh-cache |
+-------------------------------+--------------------------------------+
