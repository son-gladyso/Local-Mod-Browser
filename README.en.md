# Local MOD Browser

[中文 README](README.md)

<p align="center"><img src="docs/assets/logo-small.png" alt="Local MOD Browser logo" width="112"></p>

![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?logo=windows&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-2ea44f)
![API contract](https://img.shields.io/badge/API%20contract-2.5.0-6f42c1)
[![CI](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml/badge.svg)](https://github.com/son-gladyso/Local-Mod-Browser/actions/workflows/ci.yml)

> **Your MOD library should not be a pile of folders you are afraid to touch.**
>
> Local MOD Browser turns scattered local metadata into a searchable, comparable,
> recoverable workspace with local AI interfaces. The service itself does not upload
> your private inventory; any external AI client has its own data-sharing behavior.

[Get started](#five-minute-quick-start) · [Download v2.5.2](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2) · [AI and CLI](#ai-and-cli) · [Security boundary](#privacy-and-security) · [Open an issue](https://github.com/son-gladyso/Local-Mod-Browser/issues)

## What it is

Local MOD Browser is a privacy-first Windows catalog browser, metadata workbench,
and local AI workflow platform. It indexes directories you provide and gives you
one place to search, filter, compare, annotate, translate, favorite, and maintain
your collection over time.

It is deliberately **not** a download site, installer, mod executor, or remote
hosting service. It helps you understand and maintain the files and metadata you
already own or are authorized to use.

```text
Your metadata → index and search → details / tags / file comparison → favorites
                                               ↓
                         revisions / translation jobs / resumable batches
                                               ↓
                         browser, CLI and MCP over one local API
```

## See the product before installing

These screenshots come from the repository's **eight fictional Demo records**.
They contain no real MOD, game asset, or third-party site data; they show the actual
public build after startup rather than a design mockup.

![Public demo catalog with filters](docs/assets/demo-browse.png)

![Public demo detail panel](docs/assets/demo-detail.png)

![Public demo keyword search](docs/assets/demo-search.png)

![Public demo narrow-screen layout](docs/assets/demo-mobile.png)

See the reproducible walkthrough in [`docs/demo-walkthrough.md`](docs/demo-walkthrough.md).

![Before and after: scattered folders become a local catalog](docs/assets/before-after.svg)

### User-supplied screenshots from actual use

The following images show the user's own local library, including browsing, filtering, and detail views with a larger collection. They are not bundled data or the reproducible eight-record demo above. Item counts, game counts, and thumbnails reflect the user's environment at capture time, not content included when you install this project.

![Actual use: multi-game MOD library](docs/assets/real-use/library-overview.png)

*Card browsing across the user's multi-game library.*

![Actual use: filter by purpose](docs/assets/real-use/purpose-filters.png)

*Purpose-based filtering while keeping the catalog context visible.*

![Actual use: MOD detail panel](docs/assets/real-use/mod-detail-panel.png)

*Inspecting a single entry beside the current catalog view.*

See the [actual-use gallery](docs/real-use-gallery.md#english) for all six images and their state notes. The AI & Task Center and Download Center images record visible states in the user's local interface. They do not prove a successful task or download, or establish that the same features are included in the current public source or release.

Game and MOD names and thumbnails in these images may involve third-party rights. They do not become MIT-licensed merely because the project code uses MIT. This gallery does not distribute the underlying MODs, game assets, or source library, and does not grant permission to reuse third-party content.

## Why people use it

### Find the right thing quickly

- Search across games and local sources with full-text search, pagination, combined
  tags, author/date filters, and translation state.
- Open a stable detail view with images, source links, author text, file lists, and
  revision history instead of hunting through folders again.
- Compare the exact file copies you are considering; never assume that a MOD name
  identifies one unique archive.

### Keep decisions and maintenance work visible

- Save favorites and import/exportable loadouts for rebuilds or machine migration.
- Review metadata changes through `preview` before applying them.
- Maintain long translations as validated segments with progress, quality checks,
  pause/resume, idempotent replay, and authoritative receipts.
- Let a second assistant continue a task through leases, renewal, handoff, and
  incremental event cursors.

### Give AI a proper interface

- Browser UI, CLI, and optional MCP adapter share one contract instead of requiring
  an assistant to guess at clicks.
- The contract currently exposes 70 operations for search, details, revisions,
  favorites, loadouts, translations, and task management.
- Stable idempotency keys and receipts make retries explainable after a timeout.
- The local API binds to `127.0.0.1` by default and does not call a general-purpose
  model or silently upload your data.

## At a glance

| Need | Built-in answer |
| --- | --- |
| Search several games and drives | Multiple local sources with one indexed search surface |
| Pick one exact archive | File-level comparison and explicit selection |
| Pause a long translation | Segments, leases, receipts, checkpoints, and recovery |
| Work with an AI assistant privately | Local HTTP, CLI, or MCP with one shared contract |
| Recover after an upgrade or crash | Paired backups, restore journal, version history, and stable identities |

## Privacy and security

- Only metadata supplied by you is indexed.
- The repository does not bundle users’ source inventories, MOD archives, personal
  databases, backups, exports, or runtime tokens. Selected user-supplied interface
  screenshots are documented separately, not supplied as test data or content downloads.
- The service does not download, redistribute, install, or execute MOD files.
- The default listener is loopback-only; it is not designed as a LAN or public service.
- Default paths for runtime, database, diagnostics, exports, and test results are ignored by Git. This does not protect already-tracked files, force-added files, or data saved elsewhere; review staged changes before committing.
- Optional MCP is a local protocol interface, not an automatic remote-model connection. An external AI client may send retrieved data to its provider; check its settings and authorized scope before connecting.
- Use any third-party source only within its terms, API policy, and content license.

Read the [security policy](SECURITY.md), [contribution guide](CONTRIBUTING.md), and
[third-party notices](THIRD_PARTY_NOTICES.md) before extending the project.

## Supported platform

- Windows 10/11 x64.
- Pinned runtime: CPython 3.13.15 x64 and SQLite 3.53.4.
- The first setup downloads and verifies the pinned runtime, using a system Python
  only to run the bootstrap script.
- Sources, checksums, and licenses are recorded in [`runtime-lock.json`](runtime-lock.json).
- Linux and macOS are not currently supported.

## Five-minute quick start

### 1. Clone and create a local source configuration

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

You can also double-click `启动MOD浏览器.cmd`. The launcher prints a local URL.
The example configuration points at fictional demo metadata, so you can explore
the workflow without providing a private collection first.

If you prefer a direct download, use the [v2.5.2 Release](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2)
and download `Local-Mod-Browser-2.5.2-source.zip`. The accompanying
`SHA256SUMS.txt` lets you verify the archive.

### 3. Point it at your own metadata

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

Put a `catalog-data.json` in each `outputDir`. Relative paths are resolved from
the directory containing `sources.json`. You can also set
`LOCAL_MOD_BROWSER_SOURCES` to another configuration file.

See [`config/sources.example.json`](config/sources.example.json) and the fictional
[`examples/demo-game/catalog-data.json`](examples/demo-game/catalog-data.json).

### 4. Check the local service

```powershell
.\.runtime\python.exe -X utf8 ai.py doctor
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
```

Open `/api/docs` for the machine-readable contract and `/api/health` for runtime,
database, and service status.

## What does a first successful run look like?

Start with the fictional records: launch the service, open its local URL, search for a sample entry, inspect its details, and return to the list. You can check this small browsing loop before importing a personal collection.

Prepare Windows 10/11 x64, a system Python that can run the bootstrap script, and network access for the first pinned-runtime download. Ordinary browsing does not require AI or MCP. Developer test dependencies are documented separately in [CONTRIBUTING.md](CONTRIBUTING.md).

**Success means:** the fictional catalog is visible, search and detail views can be used, and the result of `ai.py doctor` can be inspected. Loading a page alone does not verify your source configuration, recovery behavior, or every platform operation.

## Common questions

**Why is the large library from the screenshots not included?** Those images were supplied from the user's actual environment. The bundled demo contains eight fictional records; configure your own sources separately.

**Will it discover and understand every MOD on my drives?** No. The documented input is a source configuration and a `catalog-data.json` in each `outputDir`, not universal interpretation of arbitrary folders. Check the [configuration example](config/sources.example.json) first.

**Why is the catalog empty?** Check whether `data\sources.json` is valid, which configuration directory relative paths resolve from, and whether each `outputDir` contains `catalog-data.json`. Follow the [user guide](docs/user-guide.md); do not upload a personal database to an issue.

**Is an AI connection required?** No. The browser and CLI can be used directly. Optional MCP is a local interface, not an automatic cloud-model connection. An external client you choose has its own data boundary.

**Does the real-use Download Center image prove the public version downloads MODs?** No. It shows the user's local interface with an empty list and Nexus disconnected. The public version is described here as not downloading, installing, or executing MOD files.

**Can I expose it to other devices or the internet?** The default listener is `127.0.0.1`; it is not designed as a LAN or public service. Platforms other than Windows are currently outside the supported scope.

### Find the code for your change

- Browsing and interaction: start in `static/`; cover list/detail navigation, empty/error states, and narrow layouts.
- Sources and search: start in `catalog.py` and the example configuration; use synthetic valid and invalid inputs.
- Platform operations: read `contracts.py`, `platform_api.py`, and corresponding tests together; keep HTTP, CLI, and MCP behavior aligned.
- Persistence or background jobs: read the [architecture](docs/architecture.md) first; cover interruption, retry, and recovery without weakening durability for speed.

See the [contribution guide](CONTRIBUTING.md) for commands and PR requirements, and [Roadmap and contributing](#roadmap-and-contributing) for existing starter tasks.


## AI and CLI

The CLI is a stable entry point for scripts and assistants:

```powershell
.\.runtime\python.exe -X utf8 ai.py tour
.\.runtime\python.exe -X utf8 ai.py capabilities
.\.runtime\python.exe -X utf8 ai.py games
.\.runtime\python.exe -X utf8 ai.py doctor
```

For a safe workflow:

1. Read capabilities and the contract before choosing an operation.
2. Search and read resources before preparing a `preview`.
3. Verify IDs, versions, and diffs, then apply with a stable `idempotencyKey`.
4. Wait for real terminal states; do not treat `queued` as completed.
5. After interruption, check receipts and event cursors before retrying or handing off.

See [`docs/user-guide.md`](docs/user-guide.md),
[`docs/ai-platform-guide.md`](docs/ai-platform-guide.md), and
[`docs/architecture.md`](docs/architecture.md).

## Verification

The public repository keeps reproducible synthetic acceptance checks:

```powershell
.\.runtime\python.exe -X utf8 -m unittest discover -s tests -v
.\.runtime\python.exe -X utf8 tests\startup_acceptance.py
.\.runtime\python.exe -X utf8 tests\collaboration_acceptance.py
python -m pip install jsonschema==4.26.0
python -X utf8 tests\contract_audit.py --fixture
node --check static/app.js
node --check static/editor.js
node --check tests/browser.cjs
```

Browser acceptance additionally needs `npm install` and the Playwright browser.
Windows CI runs the pinned-runtime setup, Python regression, contract audit, and
JavaScript syntax checks.

## Project map

```text
server.py                    local HTTP service and error boundary
platform_api.py              70 platform operations and business rules
contracts.py                 shared HTTP/CLI/MCP contract and schemas
catalog.py                   source configuration, indexing, and projections
ai.py                        assistant-friendly CLI
mcp_adapter.py               optional local MCP entry point
static/                      browser interface
tests/                       regression, contract, startup, collaboration, soak checks
tools/bootstrap_runtime.py   pinned runtime installation and verification
docs/                        user, AI platform, and architecture guides
```

## Roadmap and contributing

See [`ROADMAP.md`](ROADMAP.md) for the current direction. Good first contributions
include documentation, reproducible tests, accessibility improvements, and small
source-configuration enhancements.

Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) before opening a pull request.
Every external change is reviewed; CI, Code Owner approval, resolved conversations,
privacy checks, and focused tests are required before merging into `main`.

If this project solves a real problem for you, a Star or a concrete Issue helps other
people discover it. A small reproducible report is more valuable than a vague feature
request—and every accepted improvement stays reviewable in the public history.

### Start with one small improvement

For a first contribution, consider one of these existing issues:

- [First-run FAQ (#3)](https://github.com/son-gladyso/Local-Mod-Browser/issues/3): explain runtime setup, source configuration, and missing catalog files with a verification step for each failure.
- [Source configuration documentation and validation (#2)](https://github.com/son-gladyso/Local-Mod-Browser/issues/2): document fields and relative paths, then cover invalid input with synthetic tests.
- [Accessible empty and error states (#1)](https://github.com/son-gladyso/Local-Mod-Browser/issues/1): help keyboard and screen-reader users understand the current state and what to do next.

Check the latest discussion and issue status before choosing a scope. Small documentation fixes can go straight to a pull request; discuss larger features, data-model changes, and source adapters first as described in the contribution guide. You do not need to share your own MOD inventory to contribute.

## License

Project code is released under the [MIT License](LICENSE). See
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) for pinned runtime and optional
dependency notices. The MIT license does not grant rights to MODs, game assets,
site data, author text, or other third-party content.

