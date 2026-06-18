# Cahier des charges — `pptx-font-resolver`

## Objectif général

Développer un utilitaire Linux permettant d’analyser récursivement un dossier contenant des présentations PowerPoint `.pptx`, d’extraire toutes les polices utilisées, de déterminer si elles sont installées localement ou seulement substituées, puis de proposer une résolution propre via Fontconfig, Fontist, paquets système ou substitutions métriques.

Le problème visé est l’interopérabilité PowerPoint / LibreOffice Impress sous Linux : les différences de rendu proviennent souvent de polices Microsoft absentes, notamment Calibri, Cambria, Aptos, Segoe UI, MS PGothic, etc.

L’outil doit d’abord fournir une CLI robuste, puis un petit front-end local réutilisant exactement le même cœur applicatif.

---

## Contraintes générales

* Langage principal : Python 3.11+.
* CLI : `typer`.
* Affichage terminal : `rich`.
* Lecture PPTX : module standard `zipfile`, sans extraction complète du PPTX sur disque.
* Parsing rapide : extraction en bytes/regex des attributs `typeface="..."`.
* Option future possible : mode strict XML avec `lxml`, mais non obligatoire dans le MVP.
* Parallélisation : scanner les fichiers `.pptx` en parallèle.
* Cache : prévoir une base SQLite dans `~/.cache/pptx-font-resolver/index.sqlite`.
* Front-end local : FastAPI + HTMX, à implémenter après le MVP CLI.
* Ne jamais télécharger de police automatiquement sans action explicite de l’utilisateur.
* Ne jamais utiliser de sources non officielles ou douteuses pour les polices.
* Ne jamais installer les polices propriétaires globalement dans `/usr/share/fonts` ; privilégier l’installation utilisateur.

---

## Arborescence attendue

```text
pptx_font_resolver/
  __init__.py
  cli.py
  scanner.py
  pptx_parser.py
  theme_resolver.py
  fontconfig.py
  fontist_backend.py
  resolver.py
  cache.py
  report.py
  webapp.py
tests/
  test_depth_walk.py
  test_pptx_parser.py
  test_theme_resolver.py
  test_fontconfig.py
  test_reports.py
pyproject.toml
README.md
```

---

## Fonctionnalités CLI à fournir

### 1. Scanner récursivement un dossier

Commande :

```bash
pptx-font-resolver scan ./dossier
```

Options :

```bash
--depth N
--depth infinite
--jobs N
--no-cache
--format table|json|csv
--output rapport.json
--show-files
--only-missing
--all-fonts
```

Comportement attendu :

* `--depth 0` : scanne seulement le dossier donné.
* `--depth 1` : scanne le dossier + ses sous-dossiers directs.
* `--depth N` : profondeur bornée.
* `--depth infinite` : récursion complète.
* Par défaut : `--depth infinite`.
* Par défaut : `--jobs = min(8, os.cpu_count())`.

La commande doit trouver tous les `.pptx` valides sous la profondeur demandée.

---

### 2. Lister toutes les polices associées à toutes les présentations trouvées

Commande prioritaire à implémenter :

```bash
pptx-font-resolver fonts ./dossier --depth infinite
```

Cette commande doit lister toutes les polices rencontrées dans toutes les présentations trouvées, avec au minimum :

```text
Police              Statut exact       Substitution Fontconfig     Occurrences    Fichiers
Aptos               installée          Aptos                       12             4
Calibri             non installée      Carlito                     31             10
Cambria             non installée      Caladea                     8              3
Arial               installée          Arial                       22             9
MS PGothic          non installée      Noto Sans CJK JP            2              1
```

Important : distinguer clairement :

* police exactement installée ;
* police non installée mais substituée par Fontconfig ;
* police embarquée dans un PPTX ;
* police résoluble par Fontist ;
* police inconnue ;
* fallback métrique connu.

Exemple de sortie détaillée avec `--show-files` :

```text
Calibri
  statut exact       : non installée
  fc-match           : Carlito
  fallback métrique  : Carlito
  utilisée dans :
    - cours_meca.pptx
    - soutenance_finale.pptx

Aptos
  statut exact       : installée
  fc-match           : /home/jeff/.fontist/fonts/aptos/Aptos.ttf
  utilisée dans :
    - projet_2026.pptx
```

Formats exigés :

```bash
pptx-font-resolver fonts ./dossier --format table
pptx-font-resolver fonts ./dossier --format json
pptx-font-resolver fonts ./dossier --format csv
```

Le JSON doit contenir une structure exploitable par le futur front-end.

---

### 3. Rapport complet

Commande :

```bash
pptx-font-resolver report ./dossier --depth infinite --output report.html
```

Formats attendus :

```bash
--format html
--format json
--format csv
--format markdown
```

Le rapport doit contenir :

* nombre de PPTX analysés ;
* liste des PPTX ignorés ou invalides ;
* liste globale des polices ;
* statut installé/non installé ;
* substitution Fontconfig ;
* présence éventuelle de police embarquée ;
* fichiers où chaque police apparaît ;
* recommandations d’action :

  * rien à faire ;
  * installer via Fontist ;
  * installer via paquet Debian/Ubuntu ;
  * utiliser substitut métrique ;
  * import utilisateur ;
  * risque élevé pour LibreOffice.

---

### 4. Installation guidée via Fontist

Commande :

```bash
pptx-font-resolver install-font "Aptos"
```

Options :

```bash
--backend fontist
--ask-license
--accept-license
--user
--dry-run
```

Comportement :

* Par défaut, ne pas accepter automatiquement les licences.
* Pour une police Fontist qui demande une licence, lancer Fontist sans `--accept-all-licenses`, capturer la sortie, afficher le texte de licence ou le signaler, puis demander validation.
* Si l’utilisateur accepte, relancer :

```bash
fontist install --newest --accept-all-licenses "Nom Police"
```

* Appeler ensuite :

```bash
fc-cache -f
```

* Vérifier avec :

```bash
fc-match "Nom Police"
```

* Ne jamais appeler `--accept-all-licenses` sur une liste complète de polices sans validation préalable police par police.

---

### 5. Installation de toutes les polices manquantes résolubles

Commande :

```bash
pptx-font-resolver install-missing ./dossier --depth infinite --ask
```

Comportement :

* Scanner le dossier.
* Détecter les polices manquantes.
* Pour chaque police :

  * vérifier si elle est déjà exactement installée ;
  * sinon vérifier si Fontist dispose d’une formule ;
  * sinon vérifier si un paquet système connu existe ;
  * sinon proposer un fallback métrique ;
  * sinon classer comme non résolue.
* Demander confirmation police par police.
* Afficher clairement la source, le risque et le statut de licence avant toute installation.

---

## Parsing PPTX

Un `.pptx` est un ZIP. Ne jamais décompresser tout le fichier sur disque.

Lire uniquement les entrées pertinentes :

```text
ppt/theme/*.xml
ppt/slides/*.xml
ppt/slideLayouts/*.xml
ppt/slideMasters/*.xml
ppt/notesSlides/*.xml
ppt/notesMasters/*.xml
ppt/handoutMasters/*.xml
ppt/charts/*.xml
ppt/tables/*.xml
ppt/comments/*.xml
ppt/fonts/*
```

Extraction des polices :

* Chercher les attributs XML :

```xml
typeface="..."
```

* Détecter notamment :

```xml
<a:latin typeface="Aptos"/>
<a:ea typeface="Yu Gothic"/>
<a:cs typeface="Arial"/>
<a:sym typeface="Wingdings"/>
<a:font script="Jpan" typeface="Yu Gothic"/>
```

* Normaliser les noms :

  * enlever les chaînes vides ;
  * enlever les espaces superflus ;
  * ignorer les placeholders OOXML sauf pour résolution de thème.

---

## Résolution des polices de thème

PowerPoint peut utiliser des alias de thème au lieu d’un nom de police explicite :

```text
+mn-lt
+mj-lt
+mn-ea
+mj-ea
+mn-cs
+mj-cs
```

Il faut lire les fichiers :

```text
ppt/theme/theme*.xml
```

et résoudre :

```text
+mn-lt -> minorFont latin
+mj-lt -> majorFont latin
+mn-ea -> minorFont East Asian
+mj-ea -> majorFont East Asian
+mn-cs -> minorFont complex script
+mj-cs -> majorFont complex script
```

Le résultat doit distinguer :

```json
{
  "raw_fonts": ["+mn-lt", "Arial"],
  "theme_fonts": {
    "minor_latin": "Aptos",
    "major_latin": "Aptos Display"
  },
  "resolved_fonts": ["Aptos", "Arial"]
}
```

---

## Détection des polices embarquées

Détecter la présence de fichiers de polices embarquées dans le PPTX.

Ne pas les extraire automatiquement dans le MVP.

Rapporter simplement :

```text
Aptos : utilisée, non installée, mais embarquée dans presentation.pptx
```

Prévoir plus tard une option experte :

```bash
pptx-font-resolver extract-embedded ./presentation.pptx --private-cache
```

Mais cette option ne fait pas partie du MVP.

---

## Détection d’installation locale

Utiliser Fontconfig.

Pour chaque police `F` :

```bash
fc-match "F"
fc-list
```

Il faut distinguer :

* `F` exactement présente ;
* `F` absente mais substituée ;
* substitution métrique ;
* substitution générique.

Attention : `fc-match "Calibri"` peut renvoyer `Carlito`. Cela ne veut pas dire que Calibri est installée.

Implémenter une fonction :

```python
FontStatus(
    requested_family: str,
    exact_installed: bool,
    matched_family: str,
    matched_file: str | None,
    is_substituted: bool,
)
```

---

## Table de substitutions métriques connue

Inclure une table initiale :

```python
METRIC_COMPATIBLE = {
    "Calibri": ["Carlito"],
    "Cambria": ["Caladea"],
    "Arial": ["Arial", "Liberation Sans", "Arimo"],
    "Times New Roman": ["Times New Roman", "Liberation Serif", "Tinos"],
    "Courier New": ["Courier New", "Liberation Mono", "Cousine"],
}
```

Important : les substitutions métriques réduisent les risques de décalage, mais ne garantissent pas une mise en page identique. Le rapport doit le dire.

---

## Intégration Fontist

Utiliser Fontist comme backend principal pour les polices récupérables proprement.

Exemples :

```bash
fontist install --newest "Aptos"
fontist install --newest "MS PGothic"
fontist install --newest --accept-all-licenses "MS PGothic"
```

Comportement à implémenter :

1. Tester si Fontist connaît la police.
2. Si la police demande une licence, capturer la sortie.
3. Ne pas accepter automatiquement.
4. Demander validation explicite.
5. Installer seulement après validation.
6. Relancer `fc-cache`.
7. Vérifier avec `fc-match`.

Définir une abstraction :

```python
class FontistBackend:
    def status(font_name: str) -> FontistStatus: ...
    def probe_install(font_name: str) -> FontistProbeResult: ...
    def install(font_name: str, accept_license: bool) -> FontistInstallResult: ...
```

`probe_install` doit exécuter Fontist sans acceptation automatique pour récupérer le comportement :

* disponible sans licence ;
* licence requise ;
* formule absente ;
* erreur réseau ;
* erreur inconnue.

---

## Politique de licence et sécurité

Règles impératives :

* Ne pas télécharger de polices depuis des sites non officiels.
* Ne pas scraper le web à la recherche de `.ttf`.
* Ne pas modifier les fichiers de police.
* Ne pas contourner les restrictions `fsType`.
* Ne pas redistribuer de polices propriétaires.
* Installer les polices propriétaires uniquement dans un emplacement utilisateur.
* Afficher la licence ou au minimum le backend/source/licence avant validation.
* Garder une trace locale des acceptations dans le cache SQLite, par exemple :

  * nom de la police ;
  * date ;
  * backend ;
  * version éventuelle ;
  * source ;
  * hash éventuel ;
  * mode d’acceptation.

---

## Cache SQLite

Créer :

```text
~/.cache/pptx-font-resolver/index.sqlite
```

Tables proposées :

```sql
documents(
  id INTEGER PRIMARY KEY,
  path TEXT UNIQUE,
  size INTEGER,
  mtime_ns INTEGER,
  sha256 TEXT,
  scanned_at TEXT
);

document_fonts(
  document_id INTEGER,
  family TEXT,
  raw_family TEXT,
  source_xml TEXT,
  source_kind TEXT
);

font_status(
  family TEXT PRIMARY KEY,
  checked_at TEXT,
  exact_installed INTEGER,
  matched_family TEXT,
  matched_file TEXT,
  fontist_available INTEGER,
  fontist_license_required INTEGER,
  recommendation TEXT
);

license_acceptance(
  family TEXT,
  backend TEXT,
  accepted_at TEXT,
  source TEXT,
  license_label TEXT
);
```

Ne pas recalculer un PPTX si :

* chemin identique ;
* taille identique ;
* `mtime_ns` identique.

Prévoir une option :

```bash
--refresh
```

pour forcer le rescan.

---

## Parallélisation

Scanner les PPTX en parallèle au niveau fichier, pas au niveau XML.

Utiliser :

```python
concurrent.futures.ThreadPoolExecutor
```

Raison :

* beaucoup d’I/O ;
* décompression ZIP en C ;
* overhead moindre que `multiprocessing`.

Gestion :

* collecter les erreurs sans arrêter tout le scan ;
* afficher les fichiers corrompus ;
* continuer si un PPTX est invalide.

---

## Front-end local

Après le MVP CLI, créer une interface locale :

```bash
pptx-font-resolver web
```

Serveur :

```text
http://127.0.0.1:8765
```

Technos :

* FastAPI ;
* Jinja2 ;
* HTMX ;
* pas de framework JS lourd.

Écrans :

1. Choix dossier + profondeur.
2. Lancement scan.
3. Tableau des polices :

   * police ;
   * statut exact ;
   * substitution ;
   * fichiers ;
   * recommandation ;
   * bouton installer si possible.
4. Page licence :

   * police ;
   * source ;
   * backend ;
   * texte de licence capturé ;
   * bouton accepter/refuser.
5. Page rapport.

Le front-end doit appeler les mêmes fonctions Python que la CLI.

---

## Sorties attendues

### Exemple `scan`

```bash
pptx-font-resolver scan ./slides --depth 2
```

Sortie :

```text
PPTX analysés : 42
Polices uniques : 18
Polices manquantes exactes : 7
Polices embarquées détectées : 2
Polices résolubles via Fontist : 3
```

### Exemple `fonts`

```bash
pptx-font-resolver fonts ./slides --all-fonts --show-files
```

Sortie :

```text
Aptos
  statut exact : installée
  fc-match     : /home/jeff/.fontist/fonts/aptos/Aptos.ttf
  fichiers     : 4

Calibri
  statut exact      : non installée
  substitution      : Carlito
  fallback métrique : Carlito
  fichiers          : 10
  recommandation    : importer police exacte ou accepter fallback métrique

MS PGothic
  statut exact   : non installée
  substitution   : Noto Sans CJK JP
  fontist        : disponible, licence requise
  fichiers       : 1
  recommandation : installer via Fontist après acceptation licence
```

---

## Tests unitaires

Créer des tests pour :

1. Parcours récursif avec profondeur.
2. Ignorer les fichiers non `.pptx`.
3. Gérer un `.pptx` invalide sans crash.
4. Extraire `typeface="Calibri"` depuis un XML minimal.
5. Résoudre `+mn-lt` via `theme.xml`.
6. Détecter une police embarquée fictive dans `ppt/fonts/`.
7. Distinguer police exacte et substitution Fontconfig.
8. Produire JSON valide.
9. Produire CSV valide.
10. Ne pas appeler `fontist install --accept-all-licenses` sans validation explicite.

Créer quelques PPTX de test minimalistes en générant des ZIP contenant les XML nécessaires, plutôt que dépendre de vrais fichiers Office lourds.

---

## Critères d’acceptation MVP

Le MVP est accepté si :

* `pptx-font-resolver scan ./dossier --depth infinite` fonctionne.
* `pptx-font-resolver fonts ./dossier --all-fonts` liste toutes les polices associées aux présentations trouvées.
* La sortie distingue clairement :

  * installée exactement ;
  * non installée ;
  * substituée par Fontconfig ;
  * embarquée ;
  * fallback métrique connu.
* Le scan ne décompresse jamais tout le PPTX sur disque.
* Le scan est parallèle.
* Les erreurs de fichiers corrompus sont rapportées sans interrompre l’analyse.
* Le rapport JSON est exploitable par un front-end.
* L’intégration Fontist permet au moins :

  * probe d’une police ;
  * détection licence requise ;
  * installation après acceptation explicite.
* Aucune police propriétaire n’est installée sans validation explicite.

---

## Priorités de développement

### Phase 1 — cœur scanner

* walk récursif profondeur ;
* lecture ZIP ;
* extraction `typeface`;
* résolution thème ;
* agrégation par document et par police ;
* sortie table/json.

### Phase 2 — diagnostic Fontconfig

* `fc-match`;
* détection exact/substitution ;
* table fallback métrique ;
* commande `fonts`.

### Phase 3 — cache SQLite

* index documents ;
* invalidation par size + mtime_ns ;
* option `--refresh`.

### Phase 4 — Fontist

* probe ;
* licence requise ;
* installation guidée ;
* fc-cache ;
* vérification post-installation.

### Phase 5 — rapports

* CSV ;
* Markdown ;
* HTML statique.

### Phase 6 — front-end local

* FastAPI + HTMX ;
* scan ;
* tableau ;
* install guidée ;
* affichage licence.

---

## Remarques importantes

Le but n’est pas de garantir un rendu PowerPoint identique à 100 %. Le but est de réduire fortement les écarts LibreOffice/PowerPoint en identifiant et installant proprement les polices manquantes, ou en signalant les substitutions à risque.

Les substitutions métriques comme Carlito pour Calibri ou Caladea pour Cambria doivent être présentées comme des fallback de compatibilité, pas comme des équivalents parfaits.

L’outil doit être sobre, robuste, rapide, et utilisable en ligne de commande sur un gros dossier de présentations.

