# Local MOD Browser

[简体中文](../../README.md) · [English](../../README.en.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Español](README.es.md) · [Français](README.fr.md) · [Deutsch](README.de.md) · [Português (Brasil)](README.pt-BR.md)

Ces options linguistiques traduisent le README, pas l'interface de l'application ni tous les guides liés.

<p align="center"><img src="../assets/logo-small.png" alt="Logo de Local MOD Browser" width="112"></p>

![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Licence](https://img.shields.io/badge/license-MIT-2ea44f)
![Contrat d'API](https://img.shields.io/badge/API%20contract-2.5.0-6f42c1)
[![CI](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml/badge.svg)](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml)

> **Votre bibliothèque de MODs devrait être plus qu'un tas de dossiers qui s'accumulent.**
>
> Passez de « Je me souviens d'avoir ce MOD » à « Je peux le retrouver, le vérifier et reprendre mon travail en quelques secondes », grâce à un espace de travail local, interrogeable et récupérable, capable de collaborer avec l'IA.
>
> **Vous avez téléchargé un MOD, puis oublié pourquoi vous le vouliez ou à quoi il sert ?** Les résumés, descriptions de fonctions et étiquettes déjà présents vous aident à retrouver ce contexte. Vous pouvez consigner manuellement vos projets dans les notes des sélections de MODs ; le navigateur ne déduit pas automatiquement vos raisons initiales de téléchargement.

[Bien démarrer](#five-minute-quick-start) · [Télécharger la v2.5.2](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2) · [IA et ligne de commande](#ai-and-cli) · [Périmètre de sécurité](#privacy-and-security) · [Ouvrir un ticket](https://github.com/son-gladyso/Local-Mod-Browser/issues)

<a id="turn-scattered-mods-into-a-useful-personal-catalog"></a>
## Transformez des MODs dispersés en un catalogue personnel utile

Local MOD Browser est un navigateur de catalogue local de MODs pour Windows, un atelier de métadonnées et une plateforme de collaboration avec l'IA. Plutôt que de télécharger davantage de contenu pour vous, il transforme les métadonnées de répertoires que vous possédez, gérez ou êtes explicitement autorisé à utiliser en un système local que vous pouvez rechercher, filtrer, comparer, ajouter aux favoris, modifier, traduire et maintenir dans la durée.

Il vous est destiné si l'un de ces problèmes vous est familier :

- Les MODs sont éparpillés sur plusieurs disques, jeux et dossiers de sauvegarde, et retrouver un fichier prend trop de temps.
- Vous avez téléchargé des MODs, mais ne vous souvenez plus de leur rôle ou de la raison pour laquelle vous les vouliez. Les résumés, descriptions de fonctions et étiquettes déjà présents dans le catalogue vous aident à relier les fichiers à leur utilité.
- Plusieurs versions ou copies sont difficiles à comparer, et vous ne voulez pas écraser un original par erreur.
- Les favoris, l'avancement des traductions, les informations sur les auteurs et les listes de fichiers sont séparés et difficiles à récupérer après une réinstallation.
- Vous souhaitez l'aide de l'IA pour organiser vos données sans que le service téléverse vos chemins locaux, votre inventaire ou votre base de données vers un tiers. Tout client d'IA externe possède son propre comportement de partage des données.
- Des modifications ou traductions par lots interrompues ne doivent pas laisser des enregistrements à moitié écrits, des envois en double ou des états inexpliqués.

Le logiciel propose un flux de travail local clair :

```text
Your directory metadata → index and search → details / tags / file comparison → favorites / loadouts
                                                      ↓
                                     revisions / translation jobs / resumable batches
                                                      ↓
                                     browser, CLI and MCP over one local API
```

Le code source actuel prend en charge les notes sur les sélections de MODs et les champs de MOD modifiables tels que `function`, `details` et `tags`. Cela ne signifie pas qu'il existe un champ de notes « pourquoi je l'ai téléchargé » propre à chaque MOD. La récupération du contexte dépend des informations déjà présentes ou ajoutées par vous ; l'intention initiale manquante n'est pas reconstituée automatiquement.

<a id="see-the-product-before-installing"></a>
## Découvrez le produit avant de l'installer

Ces captures d'écran proviennent des **huit entrées de démonstration entièrement fictives** du dépôt. Elles ne contiennent aucun véritable MOD, aucune ressource de jeu ni aucune donnée de site tiers. Elles montrent la version publique réelle après démarrage, et non une maquette :

![Catalogue de démonstration public avec filtres](../assets/demo-browse.png)

![Panneau de détails de la démonstration publique](../assets/demo-detail.png)

![Recherche par mot-clé dans la démonstration publique](../assets/demo-search.png)

![Présentation de la démonstration publique sur écran étroit](../assets/demo-mobile.png)

Consultez le parcours reproductible complet dans [`docs/demo-walkthrough.md`](../demo-walkthrough.md).

<a id="user-supplied-screenshots-from-actual-use"></a>
### Captures d'utilisation réelle fournies par l'utilisateur

Ces images montrent la bibliothèque locale de l'utilisateur, notamment la navigation, le filtrage et les détails d'une collection plus importante. Il ne s'agit ni de données fournies avec le logiciel ni de la démonstration reproductible à huit entrées présentée ci-dessus. Les nombres d'éléments et de jeux ainsi que les vignettes reflètent l'environnement de l'utilisateur au moment de la capture, pas le contenu inclus à l'installation.

![Utilisation réelle : bibliothèque de MODs pour plusieurs jeux](../assets/real-use/library-overview.png)

*Navigation par cartes dans la bibliothèque multijeux de l'utilisateur.*

![Utilisation réelle : filtrage par usage](../assets/real-use/purpose-filters.png)

*Filtrage par usage tout en gardant visibles les cartes et le contexte des filtres.*

![Utilisation réelle : panneau de détails d'un MOD](../assets/real-use/mod-detail-panel.png)

*Examen d'une entrée à côté de la vue actuelle du catalogue.*

Les trois autres images : [fichiers et variantes](../assets/real-use/files-and-variants.png), [centre d'IA et de tâches](../assets/real-use/ai-task-center.png) et [centre de téléchargement](../assets/real-use/download-center.png).

Consultez la [galerie d'utilisation réelle](../real-use-gallery.md#english) pour les six images et leurs notes d'état. Les images du centre d'IA et de tâches et du centre de téléchargement ne font que documenter des états visibles dans l'interface locale de l'utilisateur. Elles ne prouvent pas qu'une tâche ou un téléchargement a réussi, ni que les mêmes fonctionnalités figurent dans le code source ou la version publique actuels.

Les noms de jeux et de MODs ainsi que leurs vignettes peuvent relever de droits de tiers. Leur présence dans ce dépôt ne les place pas sous licence MIT. La galerie ne distribue ni les MODs sous-jacents, ni les ressources de jeux, ni la bibliothèque source, et n'accorde aucune autorisation de réutiliser les contenus de tiers.

<a id="decide-in-30-seconds-whether-it-fits"></a>
### Décidez en 30 secondes si le logiciel vous convient

| Si vous souhaitez… | La réponse de Local MOD Browser |
| --- | --- |
| Rechercher des MODs de plusieurs jeux et disques au même endroit | Configurer plusieurs sources locales avec un index unifié interrogeable |
| Retrouver l'utilité d'un MOD téléchargé | Consulter les résumés, descriptions de fonctions et étiquettes existants ; consigner manuellement vos projets dans les notes des sélections |
| Choisir un fichier précis d'un MOD | Comparer et sélectionner explicitement les fichiers ; un ensemble entier n'est pas ajouté par défaut à une sélection |
| Suspendre et reprendre des traductions ou des travaux sur le catalogue | Tâches segmentées, baux, reçus, curseurs d'événements et récupération |
| Utiliser l'IA sans que le service téléverse votre inventaire privé | HTTP / CLI / MCP locaux, avec un contrat commun et une écoute limitée par défaut à l'interface de bouclage |
| Récupérer le travail après une migration ou une mise à niveau | Sauvegardes appariées, journal de restauration, historique des versions et identités stables des ressources |

<a id="who-is-it-for"></a>
### À qui s'adresse-t-il ?

- Aux joueurs disposant de plusieurs jeux, sources de MODs ou années de fichiers accumulés.
- Aux créateurs et responsables qui recherchent, comparent, traduisent et organisent régulièrement des informations sur les MODs.
- Aux personnes qui souhaitent une assistance de l'IA tout en gardant le contrôle des données sur leur propre ordinateur.
- À quiconque préfère une automatisation reproductible, inspectable et récupérable au fait de cliquer en espérant que tout se passe bien.

<a id="what-is-it-not"></a>
### Ce que le logiciel n'est pas

Ce n'est ni un site de téléchargement de MODs, ni un programme d'installation, ni un outil de contournement de protections, ni un service d'hébergement distant. Il ne détermine pas si un MOD est sûr, compatible ou couvert par une licence autorisant votre usage. Il organise les informations que vous possédez déjà et êtes autorisé à utiliser, en rendant chaque modification plus visible et contrôlable. Il ne télécharge, ne redistribue, n'installe et n'exécute aucun fichier de MOD.

![Avant et après : des dossiers dispersés deviennent un catalogue local](../assets/before-after.svg)

<a id="what-you-get"></a>
## Ce que vous obtenez

<a id="a-mod-browser-built-for-long-term-use"></a>
### Un navigateur de MODs conçu pour durer

- Filtrez rapidement par jeu, mots-clés, combinaisons d'étiquettes, état de traduction, auteur, date et informations de fichiers.
- Conservez une navigation stable entre listes, détails et historique, sans revenir aux dossiers pour retrouver le contexte.
- Consultez les images, les textes des auteurs, les listes de fichiers et les liens sources ; comparez des copies de fichiers précises, pas seulement les noms des MODs.
- Ajoutez les entrées importantes aux favoris et enregistrez des sélections importables et exportables pour poursuivre après une réinstallation ou un déplacement de répertoires.
- Utilisez des écrans larges ou étroits ; les filtres complexes se replient et les résultats importants restent bien visibles.

<a id="a-metadata-maintenance-workbench"></a>
### Un atelier de maintenance des métadonnées

- Examinez les modifications avec `preview` avant `apply`, afin de réduire les modifications accidentelles et les risques des opérations par lots.
- Gérez les traductions par champ et par segment, avec lots, progression, contrôles de qualité, arrêt et reprise, et réexécution idempotente.
- Les tâches d'arrière-plan prennent en charge les baux, leur renouvellement, le transfert et les curseurs d'événements, afin qu'une autre IA ou une page rouverte puisse poursuivre.
- Les écritures importantes disposent de clés d'idempotence stables et de reçus faisant autorité. Après une interruption réseau, vérifiez le résultat avant de décider de réessayer.
- SQLite utilise WAL et la synchronisation FULL, avec un journal de restauration et des sauvegardes appariées, pour privilégier l'intégrité des données.

<a id="a-local-platform-ai-can-use-correctly"></a>
### Une plateforme locale que l'IA peut utiliser correctement

- Le navigateur, la CLI et le MCP facultatif partagent un même contrat, ce qui évite à l'IA de simuler des clics dans le navigateur.
- 70 opérations stables couvrent la recherche, les détails, les révisions, les favoris, les sélections, les traductions et la gestion des tâches.
- Cinq procédures déterministes guident l'IA pour rechercher, vérifier, modifier, relire et rendre compte.
- L'API locale écoute sur `127.0.0.1` par défaut. Le service n'appelle pas de modèle généraliste et n'envoie pas automatiquement de données dans le cloud.
- En cas d'exception, les clients ne reçoivent qu'un identifiant de requête. Les journaux de diagnostic locaux sont stockés séparément pour éviter de divulguer aux appelants des chemins et des traces de pile.

<a id="core-capabilities"></a>
## Fonctionnalités principales

| Scénario | Fonctionnalités | Problème traité |
| --- | --- | --- |
| Trouver une information | Recherche plein texte, pagination, combinaisons d'étiquettes, filtres par auteur, date et état de traduction | « Je m'en souviens vaguement, mais je ne sais plus où c'est » |
| Examiner les détails | Détails, images, liens sources, listes de fichiers, historique des révisions | « Qu'est-ce qui a changé dans cette version ? » |
| Faire une sélection | Comparaison exacte de fichiers, favoris, import et export de sélections | « Il me faut cette copie, pas l'ensemble complet par erreur » |
| Modifier les métadonnées | Aperçu et application, gestion des versions, listes de champs autorisés, restauration depuis l'historique | « Un nettoyage par lots doit rester réversible » |
| Traduire | Tâches segmentées, contrôles de qualité, pause et reprise, reçus idempotents | « Un long texte interrompu ne doit pas repartir de zéro » |
| Collaborer avec l'IA | HTTP, CLI, MCP, baux, transfert, curseurs d'événements | « Permettre à plusieurs assistants de poursuivre en sécurité » |
| Protéger les données | WAL/FULL, sauvegardes appariées, journal de restauration, verrous de cycle de vie | « Récupérer après une mise à niveau ou un plantage » |

<a id="privacy-and-security"></a>
## Confidentialité et sécurité

Local MOD Browser possède des limites explicites :

- **Seules les métadonnées que vous fournissez sont indexées.** Le dépôt n'inclut pas les bibliothèques sources de MODs, archives, bases de données, sauvegardes, exports ou jetons d'exécution des utilisateurs. Les captures choisies et fournies par l'utilisateur constituent une documentation distincte, pas des données de test ni des téléchargements de contenu.
- **Il ne télécharge, ne redistribue, n'installe et n'exécute aucun MOD.** C'est un gestionnaire de métadonnées, pas un outil de téléchargement ou d'installation.
- **Il écoute localement par défaut.** Le service se lie à `127.0.0.1` et n'est pas conçu comme service pour réseau local ou public.
- **Aucun compte tiers n'est nécessaire.** Le MCP facultatif n'est qu'un point d'entrée de protocole local et n'appelle pas automatiquement un modèle distant. Un client d'IA externe peut envoyer les données récupérées à son fournisseur ; vérifiez les paramètres du client et le périmètre d'autorisation avant de le connecter.
- **Il vous incombe de disposer des autorisations concernant les données de tiers.** Respectez les conditions, la politique d'API et la licence de contenu de chaque site ou service.

Lisez la [politique de sécurité](../../SECURITY.md), le [guide de contribution](../../CONTRIBUTING.md) et les [mentions relatives aux tiers](../../THIRD_PARTY_NOTICES.md). Les chemins par défaut de l'environnement d'exécution, de la base de données, des jetons, des diagnostics, des exports et des artefacts de test figurent dans `.gitignore` pour réduire les commits accidentels. Cela ne protège pas les fichiers déjà suivis, les fichiers ajoutés de force ou les données situées ailleurs. Vérifiez toujours les modifications indexées avant de créer un commit.

<a id="supported-platform"></a>
## Plateforme prise en charge

- Windows 10/11 x64.
- Versions fixées de l'environnement d'exécution : CPython 3.13.15 x64 et SQLite 3.53.4.
- La première configuration nécessite un accès réseau pour télécharger et vérifier l'environnement d'exécution fixé ; un Python système exécute le script d'amorçage.
- Les sources, empreintes et licences de l'environnement d'exécution figurent dans [`runtime-lock.json`](../../runtime-lock.json).
- Linux et macOS ne sont pas pris en charge actuellement. Le service principal utilise la bibliothèque standard de Python, sans framework serveur supplémentaire.

<a id="five-minute-quick-start"></a>
## Démarrage rapide en cinq minutes

<a id="1-get-the-code-and-prepare-local-configuration"></a>
### 1. Récupérer le code et préparer la configuration locale

```powershell
git clone https://github.com/son-gladyso/Local-Mod-Browser.git
cd Local-Mod-Browser
New-Item -ItemType Directory -Force data | Out-Null
Copy-Item config\sources.example.json data\sources.json
```

<a id="2-install-the-pinned-runtime-and-launch"></a>
### 2. Installer l'environnement d'exécution fixé et démarrer

```powershell
python tools\bootstrap_runtime.py
.\.runtime\python.exe -X utf8 launcher.py --no-browser
```

Vous pouvez aussi double-cliquer sur `启动MOD浏览器.cmd` dans le dépôt. Le lanceur affiche une URL locale ; ouvrez-la pour explorer le catalogue de démonstration fictif et le parcours avec bibliothèque vide. Aucune véritable bibliothèque de MODs n'est nécessaire au premier démarrage.

Pour télécharger directement le code source public, utilisez `Local-Mod-Browser-2.5.2-source.zip` dans la [version v2.5.2](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2). Le fichier `SHA256SUMS.txt` qui l'accompagne permet de vérifier l'intégrité de l'archive.

<a id="3-connect-your-own-catalog"></a>
### 3. Connecter votre propre catalogue

Modifiez `data\sources.json`, qui est ignoré par Git :

```json
[
  {
    "key": "mygame",
    "title": "My Game",
    "root": "D:\\Mods\\My Game",
    "outputDir": "D:\\Mods\\My Game\\catalog"
  }
]
```

Placez un fichier `catalog-data.json` dans chaque `outputDir`. Les chemins relatifs sont résolus à partir du répertoire contenant `sources.json` ; vous pouvez aussi faire pointer `LOCAL_MOD_BROWSER_SOURCES` vers une autre configuration. Consultez [`config/sources.example.json`](../../config/sources.example.json) et [`examples/demo-game/catalog-data.json`](../../examples/demo-game/catalog-data.json).

<a id="4-check-the-service-and-local-api"></a>
### 4. Vérifier le service et l'API locale

```powershell
.\.runtime\python.exe -X utf8 ai.py doctor
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
```

Ouvrez `/api/docs` pour consulter le contrat lisible par machine et `/api/health` pour vérifier l'état de l'environnement d'exécution, de la base de données et du service.

<a id="what-does-a-first-successful-run-look-like"></a>
## À quoi ressemble un premier démarrage réussi ?

Commencez par les entrées fictives fournies, sans importer votre bibliothèque : lancez le service → ouvrez l'URL locale → recherchez un exemple → ouvrez les détails → revenez à la liste. Cette petite boucle vérifie la navigation et la recherche avant que vous n'organisiez un disque entier.

Prévoyez Windows 10/11 x64, un Python système capable d'exécuter le script d'amorçage et un accès réseau pour le premier téléchargement de l'environnement d'exécution. L'usage courant ne nécessite ni IA ni MCP ; les dépendances de test pour les développeurs figurent dans le [guide de contribution](../../CONTRIBUTING.md).

**La réussite signifie :** le catalogue fictif est visible, la recherche et les détails sont utilisables, et vous pouvez examiner les résultats de `ai.py doctor`. Le simple chargement d'une page ne vérifie ni votre propre configuration des sources, ni le comportement de récupération, ni toutes les opérations de la plateforme.

<a id="common-questions"></a>
## Questions fréquentes

**Pourquoi la grande bibliothèque montrée dans les captures manque-t-elle après le téléchargement ?** Il s'agit de captures d'utilisation réelle fournies par l'utilisateur, pas de données distribuées. Le dépôt comprend huit entrées de démonstration fictives ; configurez vos propres sources séparément.

**Le logiciel analyse-t-il et comprend-il automatiquement tous les MODs de mes disques ?** Non. Les entrées sont la configuration des sources et le fichier `catalog-data.json` de chaque `outputDir`, pas une interprétation universelle de dossiers quelconques. Vérifiez les chemins et les métadonnées par rapport à l'[exemple de configuration](../../config/sources.example.json).

**Peut-il se souvenir de la raison pour laquelle j'ai téléchargé un MOD ?** Les résumés, descriptions de fonctions et étiquettes existants vous aident à retrouver son utilité ; vous pouvez modifier les métadonnées et consigner manuellement vos projets dans les notes des sélections. Le logiciel ne peut pas déduire une intention initiale oubliée à partir des fichiers, et ce README ne promet pas de champ distinct indiquant la raison du téléchargement pour chaque MOD.

**Pourquoi la liste est-elle vide ?** Vérifiez que `data\sources.json` est valide, depuis quel répertoire de configuration les chemins relatifs sont résolus et que chaque `outputDir` cible contient `catalog-data.json`. Suivez ensuite le [guide utilisateur](../user-guide.md). Ne publiez pas de base de données privée dans un ticket.

**Dois-je connecter une IA pour naviguer ?** Non. Le navigateur et la CLI fonctionnent directement. Le MCP facultatif est une interface locale, pas un commutateur automatique vers un modèle cloud ; un client externe de votre choix possède son propre périmètre de données.

**Le centre de téléchargement des captures d'utilisation réelle montre-t-il que la version publique télécharge des MODs ?** Non. Il documente l'interface locale d'un utilisateur, avec une liste de téléchargements vide et Nexus déconnecté. La version publique reste décrite comme ne téléchargeant, n'installant et n'exécutant aucun MOD.

**Puis-je y accéder depuis d'autres appareils ou depuis Internet ?** Le service écoute sur `127.0.0.1` par défaut ; ne le déployez pas comme service pour réseau local ou public. Les plateformes autres que Windows ne sont pas non plus prises en charge actuellement.

<a id="find-the-code-for-your-change"></a>
### Trouver le code concerné par votre modification

- Navigation et interaction : commencez dans `static/` ; vérifiez les listes, les détails, les états vides et d'erreur, ainsi que le comportement sur écran étroit.
- Sources et recherche : commencez dans `catalog.py` et les exemples de configuration ; testez des entrées valides et invalides avec des catalogues synthétiques.
- Opérations de la plateforme : lisez ensemble `contracts.py`, `platform_api.py` et les tests associés pour maintenir la cohérence entre HTTP, CLI et MCP.
- Persistance ou tâches d'arrière-plan : lisez d'abord le [guide d'architecture](../architecture.md) ; couvrez les interruptions, les nouvelles tentatives et la récupération sans sacrifier la durabilité à la vitesse.

Les commandes et les exigences des demandes d'intégration figurent dans le [guide de contribution](../../CONTRIBUTING.md) ; les tâches pour débuter se trouvent dans [Feuille de route et contributions](#roadmap-and-contributing).

<a id="ai-and-cli"></a>
## IA et ligne de commande

La CLI constitue un point d'entrée stable pour les scripts et l'IA, sans simulation d'actions à la souris :

```powershell
.\.runtime\python.exe -X utf8 ai.py tour
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
.\.runtime\python.exe -X utf8 ai.py doctor
```

Procédure sûre recommandée :

1. Lisez les fonctionnalités et la documentation des interfaces pour vérifier les opérations prises en charge par cette version.
2. Recherchez et lisez les ressources avant de soumettre `preview` ; ne devinez pas l'identité d'un fichier à partir de l'ordre d'un tableau.
3. Vérifiez les identifiants de ressources, les versions et les différences dans l'aperçu, puis appliquez avec une valeur `idempotencyKey` stable.
4. Attendez les véritables états finaux des tâches d'arrière-plan, en vérifiant la relecture des résultats métier et les reçus faisant autorité. `queued` ne signifie pas terminé.
5. Après une interruption, vérifiez les reçus et les curseurs d'événements avant de poursuivre, de transférer la tâche ou de réessayer.

Consultez [`docs/user-guide.md`](../user-guide.md), [`docs/ai-platform-guide.md`](../ai-platform-guide.md) et [`docs/architecture.md`](../architecture.md).

<a id="verification-and-quality-gates"></a>
## Vérification et contrôles de qualité

Un démarrage réussi ne suffit pas à considérer le projet comme terminé. La version publique conserve des scripts de recette synthétiques reproductibles :

```powershell
# Python regression
.\.runtime\python.exe -X utf8 -m unittest discover -s tests -v

# Startup, collaboration and contract
.\.runtime\python.exe -X utf8 tests\startup_acceptance.py
.\.runtime\python.exe -X utf8 tests\collaboration_acceptance.py
python -m pip install jsonschema==4.26.0
python -X utf8 tests\contract_audit.py --fixture

# Frontend syntax
node --check static/app.js
node --check static/editor.js
node --check tests/browser.cjs
```

Les tests de recette dans le navigateur nécessitent également `npm install` et les navigateurs de Playwright. La CI Windows installe automatiquement l'environnement d'exécution fixé et effectue les tests de régression Python, l'audit du contrat et les vérifications JavaScript. Consultez le [guide de contribution](../../CONTRIBUTING.md).

<a id="project-map"></a>
## Plan du projet

```text
Local-Mod-Browser/
├─ server.py                    local HTTP service and unified error boundary
├─ platform_api.py              70 platform operations and business rules
├─ contracts.py                 shared HTTP/CLI/MCP contract and schemas
├─ catalog.py                   source configuration, indexing, and query projections
├─ ai.py                        CLI for scripts and AI
├─ mcp_adapter.py               optional local MCP entry point
├─ static/                      browser interface
├─ tests/                       regression, contract, startup, collaboration, performance and soak checks
├─ tools/bootstrap_runtime.py   pinned runtime installation and verification
└─ docs/                        user, AI platform, and architecture guides
```

<a id="roadmap-and-contributing"></a>
## Feuille de route et contributions

La version publique actuelle est `v2.5.2` et le contrat d'API est `2.5.0`. Les priorités sont les suivantes :

- Rendre le travail sur les métadonnées locales plus rapide et plus facile à examiner, sans élargir la collecte de données.
- Maintenir la cohérence entre l'API, la CLI et le MCP, avec des échecs explicables et récupérables.
- Protéger les données par des tests synthétiques et des recettes reproductibles ; ne jamais utiliser d'inventaires privés comme jeux de test publics.
- Étendre les adaptateurs de sources uniquement dans le cadre d'autorisations de contenu et de conditions de tiers clairement définies.

Consultez [`ROADMAP.md`](../../ROADMAP.md) pour l'orientation actuelle. La documentation, les tests reproductibles, l'accessibilité et les petites améliorations de la configuration des sources sont de bonnes premières contributions.

Les tickets, améliorations de documentation et demandes d'intégration sont les bienvenus. Lisez d'abord [CONTRIBUTING.md](../../CONTRIBUTING.md). Ne soumettez pas de chemins personnels, d'inventaires, de bases de données, de jetons visibles dans des captures d'écran ou de contenu tiers non autorisé. Les modifications externes sont examinées ; la CI, l'approbation du responsable du code, la résolution des discussions, les contrôles de confidentialité et les tests ciblés sont requis avant toute fusion dans `main`.

Si le logiciel résout un vrai problème, attribuez-lui une étoile, partagez-le avec quelqu'un dont les dossiers de MODs deviennent ingérables ou ouvrez un ticket concret. Un retour clair et reproductible est plus utile qu'un simple « c'est joli » ou qu'une demande vague de fonctionnalité ; les améliorations acceptées restent consultables dans l'historique public.

<a id="start-with-one-small-improvement"></a>
### Commencez par une petite amélioration

Pour une première contribution, choisissez une tâche existante :

- [FAQ du premier démarrage (#3)](https://github.com/son-gladyso/Local-Mod-Browser/issues/3) : ajoutez le dépannage de l'installation de l'environnement d'exécution, de la configuration des sources et des fichiers de catalogue manquants, avec des étapes de vérification.
- [Documentation et validation de la configuration des sources (#2)](https://github.com/son-gladyso/Local-Mod-Browser/issues/2) : expliquez les champs et les chemins relatifs, et couvrez les erreurs avec des configurations synthétiques.
- [États vides et d'erreur accessibles (#1)](https://github.com/son-gladyso/Local-Mod-Browser/issues/1) : aidez les utilisateurs du clavier et de lecteurs d'écran à comprendre l'action suivante.

Consultez la discussion et l'état actuels du ticket avant de définir votre périmètre. Les petites corrections de documentation peuvent faire directement l'objet d'une demande d'intégration ; discutez d'abord des fonctionnalités plus importantes, des changements de modèle de données et des adaptateurs de sources, conformément au guide de contribution. Vous n'avez pas besoin de fournir votre propre bibliothèque de MODs pour contribuer.

<a id="license"></a>
## Licence

Le code du projet utilise la [licence MIT](../../LICENSE). Les mentions relatives à l'environnement d'exécution tiers et aux dépendances facultatives figurent dans [`THIRD_PARTY_NOTICES.md`](../../THIRD_PARTY_NOTICES.md). La licence MIT n'accorde aucun droit sur les MODs, les ressources de jeux, les données de sites, les textes des auteurs ni aucun autre contenu de tiers.
