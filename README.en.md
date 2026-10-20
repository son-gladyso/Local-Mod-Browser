# Local MOD Browser

[简体中文](README.md) · [English](README.en.md) · [日本語](docs/i18n/README.ja.md) · [한국어](docs/i18n/README.ko.md) · [Español](docs/i18n/README.es.md) · [Français](docs/i18n/README.fr.md) · [Deutsch](docs/i18n/README.de.md) · [Português (Brasil)](docs/i18n/README.pt-BR.md)

These language options translate the README, not the application interface or every linked guide.

**Version status (2026-10-20):** The next version is undergoing separate acceptance testing and has not been released. The current public release remains `v2.5.2` (API contract `2.5.0`); the installation steps, features and security boundaries below describe that public version. New features in the development candidate or users’ local screenshots should not be treated as available in the public release.

<p align="center"><img src="docs/assets/logo-small.png" alt="Local MOD Browser logo" width="112"></p>

![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-2ea44f)
![API contract](https://img.shields.io/badge/API%20contract-2.5.0-6f42c1)
[![CI](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml/badge.svg)](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml)

> **Your MOD library should be more than a growing pile of folders.**
>
> Turn “I remember having that MOD” into “I can find it, check it, and keep working in seconds” with a local, searchable, recoverable workspace that can collaborate with AI.
>
> **Downloaded a MOD, then forgotten why you wanted it or what it does?** Existing summaries, function descriptions, and tags help you recover that context. You can manually record future plans in loadout notes; the browser does not automatically infer your original reasons for downloading anything.

[Get started](#five-minute-quick-start) · [Download v2.5.2](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2) · [AI and CLI](#ai-and-cli) · [Security boundary](#privacy-and-security) · [Open an issue](https://github.com/son-gladyso/Local-Mod-Browser/issues)

## Turn scattered MODs into a useful personal catalog

Local MOD Browser is a Windows local MOD catalog browser, metadata workbench, and AI collaboration platform. Rather than downloading more content for you, it turns metadata from directories you own, maintain, or are explicitly authorized to use into a local system you can search, filter, compare, favorite, edit, translate, and maintain over time.

It is for you if any of these problems sound familiar:

- MODs are scattered across drives, games, and backup folders, and finding one file takes too long.
- You downloaded MODs but no longer remember what each does or why you wanted it. Summaries, function descriptions, and tags already in the catalog help you reconnect the files with their purpose.
- Multiple versions or copies are hard to compare, and you do not want to overwrite an original by mistake.
- Favorites, translation progress, author information, and file lists live separately and are hard to recover after reinstalling.
- You want AI help with organization without the service uploading your local paths, inventory, or database to a third party. Any external AI client has its own data-sharing behavior.
- Interrupted batch edits or translations should not leave half-written records, duplicate submissions, or unexplained states.

It provides a clear local workflow:

```text
Your directory metadata → index and search → details / tags / file comparison → favorites / loadouts
                                                      ↓
                                     revisions / translation jobs / resumable batches
                                                      ↓
                                     browser, CLI and MCP over one local API
```

The current source supports notes on loadouts and editable MOD fields such as `function`, `details`, and `tags`. This is not a claim that there is a dedicated per-MOD “why I downloaded it” notes field. Context recovery depends on information already present or added by you; missing original intent is not automatically reconstructed.

## See the product before installing

These screenshots come from the repository's **eight entirely fictional Demo records**. They contain no real MOD, game asset, or third-party site data. They show the actual public build after startup, not a design mockup:

![Public demo catalog with filters](docs/assets/demo-browse.png)

![Public demo detail panel](docs/assets/demo-detail.png)

![Public demo keyword search](docs/assets/demo-search.png)

![Public demo narrow-screen layout](docs/assets/demo-mobile.png)

See the full reproducible walkthrough in [`docs/demo-walkthrough.md`](docs/demo-walkthrough.md).

### User-supplied screenshots from actual use

These images show the user's own local library, including browsing, filtering, and details with a larger collection. They are not bundled data or the reproducible eight-record demo above. Item counts, game counts, and thumbnails reflect the user's environment at capture time, not content included with installation.

![Actual use: multi-game MOD library](docs/assets/real-use/library-overview.png)

*Card browsing across the user's multi-game library.*

![Actual use: filter by purpose](docs/assets/real-use/purpose-filters.png)

*Purpose-based filtering while keeping cards and filter context visible.*

![Actual use: MOD detail panel](docs/assets/real-use/mod-detail-panel.png)

*Inspect a single entry beside the current catalog view.*

The other three images: [files and variants](docs/assets/real-use/files-and-variants.png), [AI & Task Center](docs/assets/real-use/ai-task-center.png), and [Download Center](docs/assets/real-use/download-center.png).

See the [actual-use gallery](docs/real-use-gallery.md#english) for all six images and their state notes. The AI & Task Center and Download Center images only record visible states in the user's local interface. They do not prove that a task or download succeeded, or that the same features are included in the current public source or release.

Game and MOD names and thumbnails may involve third-party rights. They do not become MIT-licensed by appearing in this repository. The gallery does not distribute the underlying MODs, game assets, or source library, and grants no permission to reuse third-party content.

### Decide in 30 seconds whether it fits

| If you want to… | Local MOD Browser's answer |
| --- | --- |
| Search MODs across games and drives in one place | Configure multiple local sources with a unified queryable index |
| Remember what a downloaded MOD is for | Revisit existing summaries, function descriptions, and tags; manually record plans in loadout notes |
| Select one exact file from a MOD | File-level comparison and explicit selection; a whole set is not added to a loadout by default |
| Pause and resume translations or catalog work | Segmented tasks, leases, receipts, event cursors, and recovery |
| Use AI without the service uploading your private inventory | Local HTTP / CLI / MCP with one shared contract and a loopback-only listener by default |
| Recover work after migration or an upgrade | Paired backups, restore journal, version history, and stable resource identities |

### Who is it for?

- Players with several games, MOD sources, or years of accumulated files.
- Creators and maintainers who repeatedly find, compare, translate, and organize MOD information.
- People who want AI assistance while keeping control of data on their own computer.
- Anyone who prefers reproducible, inspectable, recoverable automation to clicking and hoping.

### What is it not?

It is not a MOD download site, installer, cracking tool, or remote hosting service. It does not decide whether a MOD is safe, compatible, or licensed for your use. It organizes information you already own and are authorized to use, making each change more visible and controllable. It does not download, redistribute, install, or execute MOD files.

![Before and after: scattered folders become a local catalog](docs/assets/before-after.svg)

## What you get

### A MOD browser built for long-term use

- Filter quickly by game, keywords, combined tags, translation state, author, date, and file information.
- Keep stable navigation across lists, details, and history without returning to folders to recover context.
- View images, author text, file lists, and source links; compare specific file copies rather than MOD names alone.
- Favorite important entries and save import/exportable loadouts to continue after reinstalling or moving directories.
- Use wide or narrow screens; complex filters collapse and important results remain prominent.

### A metadata maintenance workbench

- Review changes with `preview` before `apply`, reducing accidental edits and batch-operation risks.
- Manage translations by field and segment, with batches, progress, quality checks, stop/resume, and idempotent replay.
- Background jobs support leases, renewal, handoff, and event cursors so another AI or a reopened page can continue.
- Important writes have stable idempotency keys and authoritative receipts. After network interruption, check the outcome before deciding to retry.
- SQLite uses WAL and FULL synchronization, with a restore journal and paired backups to prioritize data integrity.

### A local platform AI can use correctly

- Browser, CLI, and optional MCP share one contract, so AI need not simulate browser clicks.
- 70 stable operations cover search, details, revisions, favorites, loadouts, translations, and job management.
- Five deterministic workflows guide AI through finding, checking, changing, reading back, and reporting.
- The local API listens on `127.0.0.1` by default. The service does not call a general-purpose model or automatically send data to the cloud.
- On exceptions, clients receive only a request ID. Local diagnostic logs are stored separately to avoid leaking paths and stack traces to callers.

## Core capabilities

| Scenario | Capabilities | Problem addressed |
| --- | --- | --- |
| Find information | Full-text search, pagination, combined tags, author/date/translation-state filters | “I roughly remember it, but not where it is” |
| Inspect details | Details, images, source links, file lists, revision history | “What changed in this version?” |
| Make a selection | Exact file comparison, favorites, loadout import/export | “I need this copy, not the entire set by mistake” |
| Edit metadata | Preview/apply, versioning, field allowlists, history restoration | “Batch cleanup should still be reversible” |
| Translate | Segmented tasks, quality gates, pause/resume, idempotent receipts | “An interrupted long text should not start over” |
| Collaborate with AI | HTTP, CLI, MCP, leases, handoff, event cursors | “Let different assistants continue safely” |
| Protect data | WAL/FULL, paired backups, restore journal, lifecycle locks | “Recover after an upgrade or crash” |

## Privacy and security

Local MOD Browser has explicit boundaries:

- **Only metadata you supply is indexed.** The repository does not bundle users' source MOD libraries, archives, databases, backups, exports, or runtime tokens. Selected user-supplied screenshots are separate documentation, not test data or content downloads.
- **It does not download, redistribute, install, or execute MODs.** This is a metadata manager, not a downloader or installer.
- **It listens locally by default.** The service binds to `127.0.0.1` and is not designed as a LAN or public service.
- **No third-party account is required.** Optional MCP is only a local protocol entry point and does not automatically call a remote model. An external AI client may send retrieved data to its provider; check client settings and authorization scope before connecting.
- **You are responsible for authorizing third-party data.** Follow each site's or service's terms, API policy, and content license.

Read the [security policy](SECURITY.md), [contribution guide](CONTRIBUTING.md), and [third-party notices](THIRD_PARTY_NOTICES.md). Default paths for runtime, database, tokens, diagnostics, exports, and test artifacts are in `.gitignore` to reduce accidental commits. This does not protect already tracked files, force-added files, or data elsewhere. Always review staged changes before committing.

## Supported platform

- Windows 10/11 x64.
- Pinned runtime: CPython 3.13.15 x64 and SQLite 3.53.4.
- First setup needs network access to download and verify the pinned runtime; a system Python runs the bootstrap script.
- Runtime sources, hashes, and licenses are in [`runtime-lock.json`](runtime-lock.json).
- Linux and macOS are not currently supported. The core service uses Python's standard library without an additional backend framework.

## Five-minute quick start

### 1. Get the code and prepare local configuration

```powershell
git clone https://github.com/son-gladyso/Local-Mod-Browser.git
cd Local-Mod-Browser
New-Item -ItemType Directory -Force data | Out-Null
Copy-Item config\sources.example.json data\sources.json
```

### 2. Install the pinned runtime and launch

```powershell
python tools\bootstrap_runtime.py
.\.runtime\python.exe -X utf8 launcher.py --no-browser
```

You can also double-click `启动MOD浏览器.cmd` in the repository. The launcher prints a local URL; open it to explore the fictional demo catalog and empty-library workflow. No real MOD library is needed for the first launch.

For a direct download of the public source, use `Local-Mod-Browser-2.5.2-source.zip` from the [v2.5.2 Release](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2). The accompanying `SHA256SUMS.txt` verifies archive integrity.

### 3. Connect your own catalog

Edit the Git-ignored `data\sources.json`:

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

Place a `catalog-data.json` in each `outputDir`. Relative paths are resolved from the directory containing `sources.json`; you can also point `LOCAL_MOD_BROWSER_SOURCES` to another configuration. See [`config/sources.example.json`](config/sources.example.json) and [`examples/demo-game/catalog-data.json`](examples/demo-game/catalog-data.json).

### 4. Check the service and local API

```powershell
.\.runtime\python.exe -X utf8 ai.py doctor
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
```

Open `/api/docs` for the machine-readable contract and `/api/health` to check runtime, database, and service status.

## What does a first successful run look like?

Start with the bundled fictional records, without importing your own library: launch the service → open the local URL → search for a sample → open details → return to the list. This small loop checks browsing and search before you organize an entire drive.

Prepare Windows 10/11 x64, a system Python that can run the bootstrap script, and network access for the first runtime download. Ordinary use does not require AI or MCP; developer test dependencies are in the [contribution guide](CONTRIBUTING.md).

**Success means:** the fictional catalog is visible, search and details are usable, and you can inspect `ai.py doctor` results. Loading a page alone does not verify your own source configuration, recovery behavior, or every platform operation.

## Common questions

**Why is the large screenshot library missing after download?** Those are user-supplied actual-use screenshots, not distributed data. The repository includes eight fictional Demo records; configure your own sources separately.

**Does it automatically scan and understand every MOD on my drives?** No. Input is source configuration and `catalog-data.json` in each `outputDir`, not universal interpretation of arbitrary folders. Check paths and metadata against the [configuration example](config/sources.example.json).

**Can it remember why I downloaded a MOD?** Existing summaries, function descriptions, and tags help you revisit its purpose; you can edit metadata and manually write plans in loadout notes. It cannot infer a forgotten original intention from the files, and this README does not promise a separate per-MOD download-reason field.

**Why is the list empty?** Check that `data\sources.json` is valid, which configuration directory relative paths resolve from, and that each target `outputDir` contains `catalog-data.json`. Then follow the [user guide](docs/user-guide.md). Do not post a private database in an Issue.

**Must I connect AI to browse?** No. Browser and CLI work directly. Optional MCP is a local interface, not an automatic cloud-model switch; an external client you choose has its own data boundary.

**Does the actual-use Download Center show that the public version downloads MODs?** No. It records a user's local interface with an empty download list and Nexus disconnected. The public version remains described as not downloading, installing, or executing MODs.

**Can I access it from other devices or the internet?** It listens on `127.0.0.1` by default; do not deploy it as a LAN or public service. Platforms other than Windows are also currently unsupported.

### Find the code for your change

- Browsing and interaction: start in `static/`; verify lists, details, empty/error states, and narrow-screen behavior.
- Sources and search: start in `catalog.py` and the configuration examples; test valid and invalid inputs with synthetic catalogs.
- Platform operations: read `contracts.py`, `platform_api.py`, and related tests together to keep HTTP, CLI, and MCP aligned.
- Persistence or background jobs: read the [architecture guide](docs/architecture.md) first; cover interruption, retry, and recovery without trading durability for speed.

Commands and PR requirements are in the [contribution guide](CONTRIBUTING.md); starter tasks are under [Roadmap and contributing](#roadmap-and-contributing).

## AI and CLI

The CLI is a stable entry point for scripts and AI without simulated mouse operations:

```powershell
.\.runtime\python.exe -X utf8 ai.py tour
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
.\.runtime\python.exe -X utf8 ai.py doctor
```

Recommended safe workflow:

1. Read capabilities and interface documentation to check operations supported by this version.
2. Search and read resources before submitting `preview`; do not guess file identity from array order.
3. Check resource IDs, versions, and diffs in the preview, then apply with a stable `idempotencyKey`.
4. Wait for actual terminal states of background jobs, checking business read-back and authoritative receipts. `queued` is not completion.
5. After interruption, check receipts and event cursors before continuing, handing off, or retrying.

See [`docs/user-guide.md`](docs/user-guide.md), [`docs/ai-platform-guide.md`](docs/ai-platform-guide.md), and [`docs/architecture.md`](docs/architecture.md).

## Verification and quality gates

Starting successfully is not enough to call the project complete. The public version keeps reproducible synthetic acceptance scripts:

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

Browser acceptance additionally needs `npm install` and Playwright browsers. Windows CI automatically installs the pinned runtime and runs Python regression, contract audit, and JavaScript checks. See the [contribution guide](CONTRIBUTING.md).

## Project map

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

## Roadmap and contributing

The current public version is `v2.5.2` and API contract is `2.5.0`. Priorities are:

- Make local metadata work faster and easier to review, without expanding data collection.
- Keep API, CLI, and MCP behavior consistent, with explainable and recoverable failures.
- Protect data through synthetic tests and reproducible acceptance; never use private inventories as public fixtures.
- Extend source adapters only within clear content authorization and third-party terms.

See [`ROADMAP.md`](ROADMAP.md) for current direction. Documentation, reproducible tests, accessibility, and small source-configuration improvements are good first contributions.

Issues, documentation improvements, and Pull Requests are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) first. Do not submit personal paths, inventories, databases, tokens visible in screenshots, or unauthorized third-party content. External changes are reviewed; CI, Code Owner approval, resolved conversations, privacy checks, and focused tests are required before merging into `main`.

If it solves a real problem, give it a Star, share it with someone whose MOD folders are getting out of hand, or submit a concrete Issue. Clear reproducible feedback helps more than “looks nice” or a vague feature request; accepted improvements remain reviewable in public history.

### Start with one small improvement

For a first contribution, choose an existing task:

- [First-run FAQ (#3)](https://github.com/son-gladyso/Local-Mod-Browser/issues/3): add runtime installation, source configuration, and missing catalog-file troubleshooting with verification steps.
- [Source configuration documentation and validation (#2)](https://github.com/son-gladyso/Local-Mod-Browser/issues/2): explain fields and relative paths, and cover errors with synthetic configurations.
- [Accessible empty and error states (#1)](https://github.com/son-gladyso/Local-Mod-Browser/issues/1): help keyboard and screen-reader users understand the next action.

Check current issue discussion and status before stating your scope. Small documentation fixes can go straight to a PR; discuss larger features, data-model changes, and source adapters first, following the contribution guide. You do not need to provide your own MOD library to contribute.

## License

Project code uses the [MIT License](LICENSE). Third-party runtime and optional dependency notices are in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). MIT does not grant rights to MODs, game assets, site data, author text, or any other third-party content.
