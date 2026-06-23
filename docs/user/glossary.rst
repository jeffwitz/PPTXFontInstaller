Glossaire
========

Ce glossaire explique les termes techniques utilisés dans la documentation et l'interface.

.. contents::
   :local:

.. glossary::

   metric-compatible
      Une police qui a des **métriques similaires** (largeur des caractères, espacement, hauteur de ligne) à la police originale.
      
      *Pourquoi ?* → Moins de changements de mise en page lors de la substitution.
      
      *Exemple* : Carlito pour Calibri, Caladea pour Cambria.
      
      *Relation* : ``metric-compatible`` dans les rapports de résolution.

   visual fallback
      Une police qui a une **apparence visuelle similaire** mais des métriques différentes.
      
      *Pourquoi ?* → Alternative open-source quand la police exacte n'est pas disponible.
      
      *Risque* : Peut changer les sauts de ligne et la pagination.
      
      *Exemple* : Montserrat pour Futura PT Bold.

   Fontconfig alias
      Une règle locale qui mappe une famille de police à une autre au niveau du système Linux.
      
      *Où ?* Dans ``~/.config/fontconfig/conf.d/90-pptx-font-resolver.conf``.
      
      *Exemple* :
      
      .. code-block:: xml
      
         <alias>
           <family>Futura PT Bold</family>
           <prefer>
             <family>Montserrat</family>
           </prefer>
         </alias>
      
      *Commande* : ``pptx-font-resolver accept-fallback "Futura PT Bold" "Montserrat"``

   OOXML
      Office Open XML, le format des fichiers ``.pptx`` et ``.docx``.
      
      *Structure* : ZIP contenant des fichiers XML (ex: ``/ppt/slides/slide1.xml``).
      
      *Pourquoi ?* → Permet de scanner les polices sans extraire l'archive sur disque.

   Fontist
      Outil en ligne de commande pour installer des polices TrueType (``.ttf``) depuis des sources open-source.
      
      *Utilisation* : ``pptx-font-resolver install-font "Aptos" --accept-license``
      
      *Limite* : Certains polices propriétaires ne sont pas disponibles.

   Fontconfig
      Système de gestion des polices sous Linux qui permet de :
      
      - Détecter les polices installées
      - Gérer les substitutions (ex: Arial → Liberation Sans)
      - Configurer des alias locaux
      
      *Commandes utiles* :
      
      .. code-block:: bash
      
         fc-list | grep "Montserrat"        # Lister les polices
         fc-match "Futura PT Bold"          # Vérifier une substitution
         fc-cache -f                      # Rafraîchir le cache

   Embedded font / Police embarquée
      Une police incluse directement dans le fichier ``.pptx`` ou ``.docx``.
      
      *Détection* : ``pptx-font-resolver fonts ./documents --show-files``
      
      *Avantage* : Pas besoin d'installer la police sur le système.
      
      *Limite* : Certaines applications (LibreOffice) ne l'utilisent pas par défaut.

   Substitution / Fallback
      Quand une police demandée n'est pas disponible, Fontconfig en choisit une autre.
      
      *Types* :
      
      - **Exact** : Même famille, même style (ex: Arial → Arial)
      - **Metric-compatible** : Métriques similaires (ex: Carlito → Calibri)
      - **Visual** : Apparence similaire mais métriques différentes (ex: Montserrat → Futura PT)
      - **Generic** : Remplacement générique (ex: sans-serif → DejaVu Sans)
      - **Unsafe** : Risque élevé (ex: symbol fonts comme Wingdings)

   Risk classification / Classification des risques
      Niveau de dangerosité d'une substitution de police :
      
      - **Low** : Exact ou metric-compatible
      - **Medium** : Visual fallback
      - **High** : Substitution dangereuse (symbol fonts, CJK → Latin)
      
      *Où ?* Dans les rapports de scan et de résolution.

   Dry-run
      Mode de test qui montre ce qui serait fait **sans exécuter** les actions.
      
      *Exemple* : ``pptx-font-resolver install-missing ./documents --provider google --dry-run``
      
      *Utilité* : Vérifier les actions avant de les exécuter.

   GUI
      Interface graphique Qt (PySide6) pour scanner, résoudre et installer des polices.
      
      *Lancement* : ``pptx-font-resolver-gui``
      
      *Fonctionnalités* : Scan, résolution multi-sources, installation, export, gestion des fallbacks.

   Provider / Source de résolution
      Source utilisée pour résoudre une police manquante :
      
      - ``fontist`` : Installation via Fontist
      - ``apt`` : Installation via paquets Debian/Ubuntu
      - ``google`` : Installation via Google Fonts
      - ``local`` : Statut local via Fontconfig
      - ``all`` : Combinaison de toutes les sources
      
      *Commande* : ``pptx-font-resolver resolve ./documents --provider google``

   Ignore (session-only)
      Action dans l'interface GUI qui masque une police **uniquement pour la session en cours**.
      
      *Différence* : Contrairement à ``accept-fallback``, ``Ignore`` ne crée pas de règle persistante.
      
      *Utilité* : Masquer temporairement une police déjà traitée.

   License acceptance / Acceptation de licence
      Confirmation explicite requise pour installer certaines polices via Fontist.
      
      *Commande* : ``--accept-license`` ou confirmation GUI.
      
      *Pourquoi ?* → Respect des licences des polices.

   ZIP safety guard / Garde-fou ZIP
      Limite de taille pour éviter de scanner des archives pathologiques.
      
      *Seuil* : 500 Mo (524288000 octets)
      
      *Exemple* : ``archive uncompressed size exceeds limit: 1498762844 > 524288000``
