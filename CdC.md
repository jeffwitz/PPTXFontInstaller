Voici un **cahier des charges complet à donner à Codex** pour ajouter une solution propre aux polices absentes de Fontist dans `PPTXFontInstaller`.

---

# CdC Codex — Résolution multi-sources des polices absentes de Fontist

## 1. Objectif général

Faire évoluer `PPTXFontInstaller` pour qu’il ne dépende plus uniquement de Fontist lorsqu’une police est absente.

Le logiciel doit devenir un **résolveur de polices multi-sources** capable de classer chaque police manquante selon plusieurs stratégies :

1. police déjà installée localement ;
2. police exacte installable via Fontist ;
3. police exacte ou équivalente installable via paquet système Linux ;
4. police libre récupérable via une source connue, typiquement Google Fonts ;
5. équivalent métriquement compatible ;
6. substitution visuelle acceptable ;
7. import manuel requis ;
8. substitution déconseillée ou impossible, notamment pour les symbol fonts.

L’objectif n’est pas d’installer tout automatiquement, mais de produire une **décision typographique sûre, traçable et juridiquement propre**.

---

# 2. Principes non négociables

## 2.1. Pas d’installation propriétaire automatique

Le programme ne doit jamais télécharger ni installer automatiquement une police propriétaire hors mécanisme explicitement assumé par l’utilisateur.

Pour les polices Microsoft, Adobe, Apple ou autres familles propriétaires, le logiciel doit :

* détecter qu’elles sont absentes ;
* signaler qu’elles ne sont pas distribuables automatiquement ;
* proposer un import manuel si l’utilisateur possède légalement le fichier ;
* proposer éventuellement un équivalent libre ou un fallback visuel.

Exemple attendu :

```text
Aptos
  status: missing
  exact_source: none
  recommended_action: manual_import
  note: "Aptos is a proprietary Microsoft font. Import manually if licensed."
  visual_fallbacks: Carlito, Noto Sans, Source Sans 3
```

## 2.2. Acceptation de licence explicite

Fontist ne doit pas être appelé avec `--accept-all-licenses` par défaut.

Comportement attendu :

* par défaut : pas d’acceptation automatique ;
* option explicite CLI possible : `--accept-license`;
* GUI : confirmation explicite avant acceptation ;
* rapport : indiquer qu’une licence utilisateur est requise.

Corriger tout comportement existant qui accepterait les licences par défaut.

## 2.3. Séparer exactitude, métrique et apparence

Il faut distinguer clairement :

* **exact** : même famille typographique ;
* **metric-compatible** : famille conçue pour conserver les métriques, donc limiter les changements de mise en page ;
* **visual-substitute** : proche visuellement, mais pas garanti métriquement ;
* **generic fallback** : sans garantie forte ;
* **unsafe** : cas à risque, notamment symbol fonts.

Exemple :

```text
Calibri -> Carlito : metric-compatible
Arial -> Arimo : metric-compatible
Aptos -> Carlito : visual-substitute only
Wingdings -> Noto Sans Symbols : unsafe unless explicitly approved
```

---

# 3. Architecture cible

Ajouter une couche de résolution indépendante des backends d’installation.

Structure proposée :

```text
pptx_font_installer/
  resolver/
    __init__.py
    models.py
    engine.py
    providers.py
    curated_db.py
    manual_import.py
    distro.py
    google_fonts.py
    risk.py
  data/
    font_aliases.yml
    distro_packages.yml
    symbol_fonts.yml
```

L’objectif est de ne pas mélanger :

* analyse OOXML ;
* diagnostic Fontconfig ;
* stratégie de résolution ;
* installation ;
* import manuel ;
* génération de rapports.

---

# 4. Modèle de données

Créer ou enrichir les modèles existants avec les objets suivants.

## 4.1. `FontCandidate`

```python
from dataclasses import dataclass
from typing import Literal

RelationKind = Literal[
    "exact",
    "metric-compatible",
    "visual-substitute",
    "generic",
    "unsafe",
]

SourceKind = Literal[
    "local",
    "fontist",
    "distro-package",
    "google-fonts",
    "manual",
    "curated",
    "fontconfig",
]

@dataclass(frozen=True)
class FontCandidate:
    requested_family: str
    provided_family: str
    source: SourceKind
    relation: RelationKind
    installable: bool
    confidence: float
    install_command: list[str] | None = None
    package_name: str | None = None
    license_hint: str | None = None
    url: str | None = None
    warning: str | None = None
```

## 4.2. `FontResolution`

```python
@dataclass(frozen=True)
class FontResolution:
    requested_family: str
    exact_installed: bool
    candidates: tuple[FontCandidate, ...]
    recommended_candidate: FontCandidate | None
    recommended_action: str
    risk_level: str
    notes: tuple[str, ...]
```

`recommended_action` peut prendre les valeurs :

```python
"none"
"install_fontist"
"install_distro_package"
"install_google_font"
"install_metric_compatible"
"manual_import"
"use_visual_fallback"
"unsafe_symbol_font"
"unresolved"
```

## 4.3. `ResolutionReport`

```python
@dataclass(frozen=True)
class ResolutionReport:
    scanned_files: int
    requested_fonts: int
    missing_fonts: int
    resolved_exact: int
    resolved_metric: int
    manual_required: int
    unsafe: int
    resolutions: tuple[FontResolution, ...]
```

---

# 5. Chaîne de résolution

Implémenter un moteur central :

```python
class FontResolutionEngine:
    def __init__(self, providers: list[FontProvider]):
        self.providers = providers

    def resolve_family(self, family: str) -> FontResolution:
        ...

    def resolve_many(self, families: Iterable[str]) -> ResolutionReport:
        ...
```

Ordre recommandé des providers :

```python
providers = [
    LocalFontProvider(),
    FontistProvider(),
    DistroPackageProvider(),
    GoogleFontsProvider(),
    CuratedFallbackProvider(),
    FontconfigFallbackProvider(),
    ManualImportProvider(),
]
```

Le moteur doit :

1. normaliser le nom de famille ;
2. vérifier l’installation locale exacte ;
3. interroger Fontist ;
4. chercher un paquet système ;
5. chercher dans la base Google Fonts locale ou distante ;
6. chercher dans la base de correspondances typographiques ;
7. chercher la substitution actuelle Fontconfig ;
8. produire une recommandation finale ;
9. attribuer un niveau de risque.

---

# 6. Providers à implémenter

## 6.1. `LocalFontProvider`

Utilise Fontconfig.

Doit vérifier :

```bash
fc-list
fc-match
```

Contraintes :

* ne pas appeler `fc-list` pour chaque police ;
* créer un cache en mémoire ;
* normaliser les noms de famille ;
* exposer la police exacte installée ou la substitution Fontconfig.

Exemple d’API :

```python
class LocalFontProvider(FontProvider):
    def candidates_for(self, family: str) -> list[FontCandidate]:
        ...
```

## 6.2. `FontistProvider`

Réutiliser le backend existant, mais sous forme de provider.

Le provider doit pouvoir répondre à deux questions :

```python
is_available(family: str) -> bool
install_command(family: str) -> list[str]
```

Ne pas installer directement depuis le provider. Le provider propose un candidat, le moteur décide, puis la CLI/GUI demande confirmation.

Corriger le comportement licence :

```text
Default: no --accept-all-licenses
With explicit option: --accept-all-licenses
```

## 6.3. `DistroPackageProvider`

Objectif : proposer des paquets Linux connus.

V1 : Debian/Ubuntu uniquement.

Créer un fichier :

```text
pptx_font_installer/data/distro_packages.yml
```

Exemple :

```yaml
Calibri:
  metric_compatible:
    - family: Carlito
      package: fonts-crosextra-carlito
      distro: debian
      relation: metric-compatible
      license: OFL-1.1

Cambria:
  metric_compatible:
    - family: Caladea
      package: fonts-crosextra-caladea
      distro: debian
      relation: metric-compatible
      license: OFL-1.1

Arial:
  metric_compatible:
    - family: Arimo
      package: fonts-croscore
      distro: debian
      relation: metric-compatible
    - family: Liberation Sans
      package: fonts-liberation
      distro: debian
      relation: metric-compatible

Times New Roman:
  metric_compatible:
    - family: Tinos
      package: fonts-croscore
      distro: debian
      relation: metric-compatible
    - family: Liberation Serif
      package: fonts-liberation
      distro: debian
      relation: metric-compatible

Courier New:
  metric_compatible:
    - family: Cousine
      package: fonts-croscore
      distro: debian
      relation: metric-compatible
    - family: Liberation Mono
      package: fonts-liberation
      distro: debian
      relation: metric-compatible

Noto Sans CJK SC:
  exact_or_family:
    - family: Noto Sans CJK SC
      package: fonts-noto-cjk
      distro: debian
      relation: exact
```

La CLI ne doit pas lancer `sudo apt install` automatiquement par défaut. Elle doit proposer :

```bash
sudo apt install fonts-crosextra-carlito fonts-crosextra-caladea fonts-noto-cjk
```

Option possible :

```bash
pptx-font-installer install-missing ./docs --provider apt --execute
```

Même avec `--execute`, demander confirmation sauf option explicite `--yes`.

## 6.4. `GoogleFontsProvider`

Objectif : proposer des familles libres disponibles dans Google Fonts.

V1 simple :

* utiliser une base locale générée ou un petit index JSON versionné ;
* ne pas faire de scraping web en temps réel ;
* ne pas télécharger sans confirmation ;
* indiquer la licence.

Structure possible :

```text
pptx_font_installer/data/google_fonts_index.json
```

Exemple minimal :

```json
{
  "Roboto": {
    "family": "Roboto",
    "license": "Apache-2.0",
    "source": "google-fonts"
  },
  "Noto Sans": {
    "family": "Noto Sans",
    "license": "OFL-1.1",
    "source": "google-fonts"
  }
}
```

V1 : seulement proposer le candidat, sans forcément télécharger.

V2 : téléchargement contrôlé depuis une URL officielle ou via dépôt Google Fonts.

## 6.5. `CuratedFallbackProvider`

Provider fondamental.

Créer :

```text
pptx_font_installer/data/font_aliases.yml
```

Contenu initial recommandé :

```yaml
Calibri:
  manual:
    note: "Proprietary Microsoft font. Use manual import if licensed."
  metric_compatible:
    - family: Carlito
      source: distro-package
      package: fonts-crosextra-carlito
      license: OFL-1.1

Cambria:
  manual:
    note: "Proprietary Microsoft font. Use manual import if licensed."
  metric_compatible:
    - family: Caladea
      source: distro-package
      package: fonts-crosextra-caladea
      license: OFL-1.1

Arial:
  metric_compatible:
    - family: Arimo
      source: distro-package
      package: fonts-croscore
    - family: Liberation Sans
      source: distro-package
      package: fonts-liberation

Times New Roman:
  metric_compatible:
    - family: Tinos
      source: distro-package
      package: fonts-croscore
    - family: Liberation Serif
      source: distro-package
      package: fonts-liberation

Courier New:
  metric_compatible:
    - family: Cousine
      source: distro-package
      package: fonts-croscore
    - family: Liberation Mono
      source: distro-package
      package: fonts-liberation

Aptos:
  manual:
    note: "Recent Microsoft font. No guaranteed free metric-compatible replacement."
  visual_substitute:
    - family: Carlito
    - family: Noto Sans
    - family: Source Sans 3

Aptos Display:
  manual:
    note: "Recent Microsoft font. Manual import recommended if exact rendering is required."
  visual_substitute:
    - family: Source Sans 3
    - family: Noto Sans

Segoe UI:
  manual:
    note: "Microsoft font. Manual import recommended if exact rendering is required."
  visual_substitute:
    - family: Noto Sans
    - family: Liberation Sans
    - family: DejaVu Sans

Helvetica:
  visual_substitute:
    - family: Liberation Sans
    - family: Arimo
    - family: Noto Sans
```

## 6.6. `ManualImportProvider`

Objectif : gérer les polices que l’utilisateur fournit lui-même.

Commande cible :

```bash
pptx-font-installer import-font ./Aptos.ttf
pptx-font-installer import-fonts ./fonts/
```

Comportement attendu :

1. accepter `.ttf`, `.otf`, `.ttc` ;
2. lire le nom réel de famille avec `fontTools`;
3. comparer avec les polices manquantes ;
4. copier dans :

```bash
~/.local/share/fonts/pptx-font-installer/
```

5. lancer :

```bash
fc-cache -f ~/.local/share/fonts
```

6. relancer un diagnostic Fontconfig ;
7. afficher le résultat.

Dépendance optionnelle :

```toml
[project.optional-dependencies]
font-import = [
  "fonttools>=4.0",
]
```

En cas d’absence de `fontTools`, message clair :

```text
Manual font import requires the optional dependency:
pip install PPTXFontInstaller[font-import]
```

---

# 7. Gestion des symbol fonts

Créer :

```text
pptx_font_installer/data/symbol_fonts.yml
```

Contenu initial :

```yaml
symbol_fonts:
  - Symbol
  - Wingdings
  - Wingdings 2
  - Wingdings 3
  - Webdings
  - MS Gothic Symbols
```

Règles :

* ne jamais appliquer automatiquement un fallback générique ;
* classer en risque élevé ;
* indiquer que les glyphes peuvent changer de sens ;
* proposer import manuel ou validation explicite.

Exemple attendu :

```text
Wingdings
  risk: high
  recommended_action: unsafe_symbol_font
  note: "Symbol font: automatic substitution may alter glyph semantics."
```

---

# 8. CLI cible

## 8.1. Commande `resolve`

Nouvelle commande :

```bash
pptx-font-installer resolve ./presentations
```

Options :

```bash
--depth N
--jobs N
--format table|json|csv|markdown
--output report.json
--all-fonts
--only-missing
--only-actionable
--provider fontist|apt|google|manual|all
--distro debian|ubuntu
```

Sortie table :

```text
Family              Status      Best action                 Risk
Calibri             missing     install Carlito             medium
Aptos               missing     manual import               medium
Wingdings           missing     manual import / unsafe      high
Noto Sans CJK SC    missing     install fonts-noto-cjk      medium
Arial               resolved    use Arimo/Liberation Sans   low
```

## 8.2. Commande `install-missing`

Étendre l’existant.

```bash
pptx-font-installer install-missing ./presentations --provider fontist
pptx-font-installer install-missing ./presentations --provider apt
pptx-font-installer install-missing ./presentations --provider all
```

Comportement :

* liste les actions ;
* demande confirmation ;
* n’exécute rien si `--dry-run`;
* ne lance `sudo apt install` que si `--execute`;
* ne passe `--accept-all-licenses` que si `--accept-license`.

Options :

```bash
--dry-run
--execute
--yes
--accept-license
--provider fontist|apt|google|all
```

## 8.3. Commande `import-font`

```bash
pptx-font-installer import-font ./Aptos.ttf
```

Options :

```bash
--target ~/.local/share/fonts/pptx-font-installer
--refresh-cache
--check-again ./presentations
```

## 8.4. Commande `import-fonts`

```bash
pptx-font-installer import-fonts ./fonts/
```

Options :

```bash
--recursive
--dry-run
--copy
--symlink
--refresh-cache
```

## 8.5. Commande `explain`

```bash
pptx-font-installer explain "Calibri"
pptx-font-installer explain "Aptos"
pptx-font-installer explain "Wingdings"
```

Sortie :

```text
Requested font: Calibri

Exact font:
  Not installed.
  Not available through configured free providers.

Recommended:
  Carlito
  Relation: metric-compatible
  Source: Debian/Ubuntu package
  Package: fonts-crosextra-carlito

Manual import:
  Recommended only if exact Microsoft rendering is required.
```

---

# 9. Rapports

Mettre à jour les formats JSON/CSV/Markdown.

## 9.1. JSON

Exemple :

```json
{
  "summary": {
    "scanned_files": 42,
    "requested_fonts": 31,
    "missing_fonts": 8,
    "manual_required": 2,
    "unsafe": 1
  },
  "resolutions": [
    {
      "requested_family": "Calibri",
      "exact_installed": false,
      "risk_level": "medium",
      "recommended_action": "install_metric_compatible",
      "recommended_candidate": {
        "provided_family": "Carlito",
        "source": "distro-package",
        "relation": "metric-compatible",
        "installable": true,
        "package_name": "fonts-crosextra-carlito",
        "install_command": [
          "sudo",
          "apt",
          "install",
          "fonts-crosextra-carlito"
        ],
        "license_hint": "OFL-1.1"
      }
    }
  ]
}
```

## 9.2. CSV

Colonnes minimales :

```text
requested_family
status
risk_level
recommended_action
recommended_family
relation
source
package_name
install_command
license_hint
warning
files
```

## 9.3. Markdown

Exemple :

```markdown
## Missing fonts resolution report

| Requested | Action | Recommended | Relation | Source | Risk |
|---|---|---|---|---|---|
| Calibri | install metric-compatible | Carlito | metric-compatible | apt | medium |
| Aptos | manual import | — | — | manual | medium |
| Wingdings | unsafe | — | — | manual | high |
```

---

# 10. GUI cible

Ajouter dans la GUI :

## 10.1. Colonnes

```text
Family
Installed
Fontist
Recommended action
Recommended family
Relation
Source
Risk
Files
```

## 10.2. Boutons

Pour une police sélectionnée :

```text
[Explain]
[Install via Fontist]
[Install system package]
[Import font file]
[Accept fallback]
[Ignore]
```

Pour l’ensemble :

```text
[Resolve all]
[Install safe recommendations]
[Export report]
```

## 10.3. Règles GUI

* ne jamais installer une symbol font automatiquement ;
* afficher une confirmation pour toute acceptation de licence ;
* afficher une confirmation avant toute commande `apt`;
* afficher clairement la différence entre police exacte et fallback ;
* permettre l’import manuel par sélection de fichier `.ttf/.otf/.ttc`.

---

# 11. Corrections à intégrer en même temps

## 11.1. Corriger `--all-fonts`

Le comportement actuel semble ambigu. Spécification attendue :

* par défaut : afficher les polices problématiques ;
* `--only-missing` : afficher uniquement les familles non installées exactement ;
* `--all-fonts` : afficher toutes les familles, y compris celles installées exactement.

Pseudo-code :

```python
if only_missing:
    summaries = [
        s for s in summaries
        if not s.status.exact_installed
    ]
elif not all_fonts:
    summaries = [
        s for s in summaries
        if s.risk_level != "none" or not s.status.exact_installed
    ]
```

## 11.2. Cache Fontconfig

Ne pas rappeler `fc-list` pour chaque police.

Créer :

```python
class FontconfigCache:
    def __init__(self):
        self.installed_families = load_fc_list_once()

    def is_exact_installed(self, family: str) -> bool:
        ...

    def match(self, family: str) -> FontconfigMatch:
        ...
```

## 11.3. Garde-fous ZIP

Ajouter limites de sécurité :

```python
MAX_XML_SIZE = 20 * 1024 * 1024
MAX_ARCHIVE_UNCOMPRESSED_SIZE = 500 * 1024 * 1024
MAX_ARCHIVE_ENTRIES = 10000
```

Si dépassement :

* ne pas planter ;
* ajouter un warning au rapport ;
* continuer les autres fichiers.

---

# 12. Tests à ajouter

## 12.1. Tests unitaires moteur

Créer :

```text
tests/test_resolution_engine.py
```

Cas :

```text
Calibri -> Carlito metric-compatible
Cambria -> Caladea metric-compatible
Aptos -> manual import + visual fallback
Wingdings -> unsafe symbol font
UnknownFontXYZ -> unresolved
```

## 12.2. Tests provider distro

```text
tests/test_distro_provider.py
```

Vérifier :

* `fonts-crosextra-carlito` proposé pour Calibri ;
* `fonts-crosextra-caladea` proposé pour Cambria ;
* `fonts-noto-cjk` proposé pour familles Noto CJK ;
* pas de commande `sudo apt install` exécutée en dry-run.

## 12.3. Tests manual import

```text
tests/test_manual_import.py
```

Avec font factice ou mock `fontTools`.

Vérifier :

* extension acceptée ;
* nom de famille lu ;
* copie dans le bon dossier ;
* appel à `fc-cache` mocké ;
* erreur claire si `fontTools` absent.

## 12.4. Tests licences

```text
tests/test_fontist_license_policy.py
```

Vérifier :

* `--accept-all-licenses` absent par défaut ;
* présent seulement avec option explicite ;
* GUI ne passe pas `accept_license=True` sans confirmation.

## 12.5. Tests rapports

```text
tests/test_resolution_reports.py
```

Vérifier :

* JSON contient `recommended_action`;
* CSV contient `relation`;
* Markdown distingue exact/metric/visual/manual/unsafe.

## 12.6. Tests CLI

```text
tests/test_cli_resolve.py
```

Scénarios :

```bash
resolve ./fixtures --format json
resolve ./fixtures --only-missing
resolve ./fixtures --all-fonts
explain Calibri
explain Wingdings
import-font ./fixture-font.ttf --dry-run
```

---

# 13. Documentation à mettre à jour

## 13.1. README

Ajouter une section :

```markdown
## Fonts not available through Fontist
```

Contenu à expliquer :

* Fontist n’est qu’une source ;
* certaines polices sont propriétaires ;
* le logiciel propose des équivalents libres ;
* les équivalents métriques limitent les changements de mise en page ;
* les substitutions visuelles ne garantissent pas la mise en page ;
* les symbol fonts sont dangereuses à remplacer ;
* l’import manuel est prévu pour les utilisateurs qui possèdent légalement une police.

## 13.2. Exemples

Ajouter :

```bash
pptx-font-installer resolve ./slides
pptx-font-installer resolve ./slides --format markdown --output font-report.md
pptx-font-installer install-missing ./slides --provider apt --dry-run
pptx-font-installer import-font ~/Downloads/Aptos.ttf
pptx-font-installer explain Calibri
```

## 13.3. Avertissement licence

Ajouter :

```markdown
This tool does not redistribute proprietary fonts.
Manual import is provided only for users who already have the right to use the font files.
License acceptance is never automatic unless explicitly requested by the user.
```

---

# 14. Critères d’acceptation

La tâche est considérée terminée si :

1. `resolve` produit une recommandation pour chaque police absente ;
2. Fontist reste utilisable mais n’est plus l’unique source ;
3. Calibri propose Carlito comme équivalent métrique ;
4. Cambria propose Caladea comme équivalent métrique ;
5. Aptos est classée en import manuel recommandé, avec fallbacks visuels ;
6. Wingdings est classée à haut risque ;
7. les rapports JSON/CSV/Markdown contiennent la source, la relation et l’action recommandée ;
8. aucune licence Fontist n’est acceptée automatiquement par défaut ;
9. l’import manuel `.ttf/.otf/.ttc` fonctionne ou échoue proprement ;
10. les tests unitaires et CLI passent ;
11. la documentation explique clairement les limites juridiques et typographiques.

---

# 15. Découpage de travail recommandé pour Codex

## Étape 1 — Refactor modèle

* créer `resolver/models.py`;
* créer `FontCandidate`, `FontResolution`, `ResolutionReport`;
* ajouter tests unitaires simples.

## Étape 2 — Base YAML

* créer `font_aliases.yml`;
* créer `symbol_fonts.yml`;
* créer `distro_packages.yml`;
* créer loader YAML robuste.

Ajouter dépendance :

```toml
PyYAML >= 6.0
```

ou utiliser `tomllib` si passage en TOML préféré. YAML est plus lisible pour ce type de base.

## Étape 3 — Providers

* `LocalFontProvider`;
* `FontistProvider`;
* `DistroPackageProvider`;
* `CuratedFallbackProvider`;
* `ManualImportProvider`.

Ne pas commencer par Google Fonts si cela complexifie trop. Google Fonts peut être V2.

## Étape 4 — Moteur de résolution

* implémenter ordre de priorité ;
* trier les candidats ;
* choisir une recommandation ;
* attribuer un risque.

## Étape 5 — CLI

* ajouter `resolve`;
* ajouter `explain`;
* étendre `install-missing`;
* ajouter `import-font`;
* ajouter `import-fonts`.

## Étape 6 — Rapports

* enrichir JSON ;
* enrichir CSV ;
* enrichir Markdown ;
* maintenir compatibilité avec les rapports existants si possible.

## Étape 7 — GUI

* afficher recommandation ;
* ajouter boutons ;
* ajouter import manuel ;
* ajouter confirmations licence/apt.

## Étape 8 — Tests et documentation

* tests unitaires ;
* tests CLI ;
* README ;
* exemples ;
* notes de licence.

---

# 16. Prompt prêt à donner à Codex

```text
Tu travailles sur le dépôt jeffwitz/PPTXFontInstaller.

Objectif :
Ajouter une couche de résolution multi-sources pour les polices absentes, afin que l’outil ne dépende plus uniquement de Fontist.

Contexte :
Le projet scanne déjà les fichiers PPTX/DOCX, extrait les familles de polices, interroge Fontconfig, génère des rapports et propose une intégration Fontist. Il faut maintenant gérer les cas où Fontist ne fournit pas la police demandée.

Contraintes fortes :
- Ne jamais redistribuer ni télécharger automatiquement une police propriétaire.
- Ne jamais accepter automatiquement une licence Fontist par défaut.
- Distinguer clairement :
  - exact
  - metric-compatible
  - visual-substitute
  - generic
  - unsafe
- Les symbol fonts doivent être classées à haut risque et ne jamais être substituées automatiquement.
- L’import manuel doit être possible pour les utilisateurs qui possèdent légalement un fichier .ttf/.otf/.ttc.
- Les commandes système de type apt doivent être proposées en dry-run par défaut, pas exécutées sans confirmation.

Travail demandé :
1. Créer un module pptx_font_installer/resolver/ avec :
   - models.py
   - engine.py
   - providers.py
   - distro.py
   - curated_db.py
   - manual_import.py
   - risk.py

2. Ajouter les modèles :
   - FontCandidate
   - FontResolution
   - ResolutionReport

3. Ajouter des bases de données locales :
   - data/font_aliases.yml
   - data/distro_packages.yml
   - data/symbol_fonts.yml

4. Implémenter les providers :
   - LocalFontProvider
   - FontistProvider
   - DistroPackageProvider
   - CuratedFallbackProvider
   - ManualImportProvider

5. Implémenter FontResolutionEngine avec l’ordre :
   - local exact
   - Fontist exact
   - distro package exact/metric
   - curated fallback
   - fontconfig fallback
   - manual import
   - unresolved

6. Ajouter les commandes CLI :
   - resolve PATH
   - explain FAMILY
   - import-font FILE
   - import-fonts DIR
   - étendre install-missing avec --provider fontist|apt|all, --dry-run, --execute, --yes, --accept-license

7. Mettre à jour les rapports JSON/CSV/Markdown avec :
   - requested_family
   - exact_installed
   - recommended_action
   - recommended_family
   - relation
   - source
   - package_name
   - install_command
   - license_hint
   - risk_level
   - warning

8. Corriger le comportement de --all-fonts / --only-missing si nécessaire :
   - par défaut : afficher les polices problématiques ;
   - --only-missing : seulement les polices non installées exactement ;
   - --all-fonts : toutes les polices.

9. Corriger la politique Fontist :
   - ne jamais passer --accept-all-licenses par défaut ;
   - ne le faire que si --accept-license est explicitement fourni ;
   - dans la GUI, demander confirmation explicite.

10. Ajouter un cache Fontconfig pour éviter d’appeler fc-list pour chaque police.

11. Ajouter des garde-fous ZIP :
   - taille XML maximale ;
   - nombre maximal d’entrées ;
   - taille décompressée totale maximale ;
   - warning plutôt que crash.

12. Ajouter les tests :
   - Calibri -> Carlito metric-compatible
   - Cambria -> Caladea metric-compatible
   - Arial -> Arimo/Liberation Sans
   - Times New Roman -> Tinos/Liberation Serif
   - Courier New -> Cousine/Liberation Mono
   - Aptos -> manual_import + visual fallback
   - Wingdings -> unsafe_symbol_font
   - UnknownFontXYZ -> unresolved
   - Fontist n’accepte pas les licences par défaut
   - import manuel avec fontTools mocké
   - rapports JSON/CSV/Markdown enrichis
   - CLI resolve/explain/import-font

13. Mettre à jour le README :
   - expliquer les limites de Fontist ;
   - expliquer les équivalents métriques ;
   - expliquer l’import manuel ;
   - expliquer les risques des symbol fonts ;
   - ajouter des exemples CLI.

Critères d’acceptation :
- La commande `pptx-font-installer resolve ./docs` produit une recommandation pour chaque police.
- Calibri propose Carlito.
- Cambria propose Caladea.
- Aptos demande un import manuel.
- Wingdings est marqué high risk.
- Les rapports contiennent relation/source/action recommandée.
- Aucune licence n’est acceptée automatiquement.
- Les tests passent.
```

Ce CdC est volontairement assez strict : il évite que Codex parte vers une solution “magique” de téléchargement de polices, et l’oblige à produire une chaîne de décision typographique robuste.

