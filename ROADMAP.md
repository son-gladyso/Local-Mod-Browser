# Roadmap

Local MOD Browser is intentionally focused on local ownership, predictable recovery,
and explainable automation. This roadmap is directional rather than a promise of
dates; priorities can change when real user feedback exposes a more important problem.

## Now — make the first run effortless

- Improve first-run guidance for an empty catalog and invalid source configuration.
- Add a concise FAQ for runtime bootstrap, path mapping, indexing, and backup recovery.
- Keep the public demo fixture small, fictional, and safe to run in CI.
- Turn recurring support questions into reproducible documentation or tests.

## Next — make daily catalog work faster

- Add clearer saved-search and filter-link workflows.
- Improve keyboard navigation and accessibility feedback for empty, loading, and error states.
- Add more focused import/export examples without bundling private or third-party content.
- Provide richer local diagnostics that remain safe to show in issue reports.

## Later — extend collaboration without weakening the boundary

- Add opt-in source adapters that operate only on user-supplied, authorized metadata.
- Improve MCP examples for task handoff, receipts, and incremental event reading.
- Add migration helpers for larger collections and explicit dry-run reports.
- Evaluate optional signed release artifacts and reproducible build metadata.

## Not planned

- Hosting or redistributing MOD archives.
- A remote account requirement or a cloud inventory service.
- Automatic MOD installation, execution, or compatibility claims.
- Scraping or bulk-rehosting third-party site data.

## How to influence the roadmap

Open an Issue with a concrete problem, a minimal reproduction, and the behavior you
would consider successful. Small documentation and test improvements are especially
good first contributions; look for the `good first issue` label. Current starter tasks:

- [Add a first-run FAQ](https://github.com/son-gladyso/Local-Mod-Browser/issues/3)
- [Improve empty and error states](https://github.com/son-gladyso/Local-Mod-Browser/issues/1)
- [Document and validate source files](https://github.com/son-gladyso/Local-Mod-Browser/issues/2)
