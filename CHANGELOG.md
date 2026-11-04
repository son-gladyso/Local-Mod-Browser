# Changelog

## Unreleased

- Fixed the MOD detail panel: Close and Esc now return to the list even after switching MOD inside the
  panel, and a page opened from a `?detail=` link closes in place instead of navigating away.
- The whole card opens the detail preview, the open card is highlighted, and the panel can step to the
  previous/next MOD on the page with `‹ ›` buttons or the ←/→ keys while keeping the current tab.
- Buttons that start slow work show progress and ignore repeated presses until the work settles.
- Everyday filters stay visible while less-used ones fold under “更多条件” with an active-count badge.
- Clearer empty states with a direct path back to the library, profile-card click to open, removal
  feedback, a back-to-top button, view switches that land at the top, and tap-outside to close the
  narrow-screen menu.

- New Nexus-inspired visual theme (`static/theme.css`): compact black top bar, dark content canvas
  with darker navigation bands, classic orange accent, Nexus-style tab bars with orange counts, light
  grey tag pills, tile footers with download/endorsement/update stats, a detail masthead that uses
  the MOD's first local image as a banner with an icon stat strip, and file lists grouped into
  主文件 / 可选文件 / … with a header row (upload date, size, version) per file. All styles and
  icons are written for this project; no Nexus Mods CSS, fonts, icons or images are included.

- Navigation moved from the left sidebar into a Nexus-style top bar: the main menu sits next to the
  logo (current entry underlined in orange) and a second row switches games; on narrow screens the
  same entries open as a menu drawer. The bundled Inter font (SIL OFL 1.1) is used for Latin text
  with the system's CJK font for Chinese, without extra letter spacing or tagline labels.

- The library follows the redesigned Nexus mods listing: near-black page, filters in a left column
  (用途 as a checkbox list with counts, a 隐藏筛选 toggle), dark sort/page-size pills, and tiles laid out
  as title, author, category, update date, summary and an endorsement/download footer.

The API contract is unchanged; these are browser interface improvements only.

## 2.5.2 - 2026-09-22

- Added a reproducible public Demo walkthrough with eight fictional records.
- Added real browser screenshots for desktop, detail, search, and narrow-screen views.
- Added a before/after catalog illustration and a compact project logo.

The API contract remains `2.5.0`; this patch release adds public demonstration assets
and does not change the local protocol.

## 2.5.1 - 2026-09-22

- Added a complete English README and a project social-preview asset.
- Added a public roadmap, documentation issue template, CODEOWNERS, and reviewed-PR guidance.
- Added a source ZIP release workflow for easier first-time downloads.

The API contract remains `2.5.0`; this patch release improves public packaging,
documentation, and contribution ergonomics without changing the contract.

## 2.5.0 - 2026-09-21

- Added a unified 70-operation HTTP/CLI/MCP contract.
- Added resumable batched imports, authoritative receipts and atomic translation
  publication.
- Added fair foreground/background write scheduling and bounded performance
  metrics.
- Added paired database backup/recovery with lifecycle locking.
- Added deterministic workflow execution, leases, handoff and event cursors.
- Added combined tag filters, stable navigation, file comparison and responsive
  Nexus-style browsing.
- Added a pinned Windows CPython/SQLite runtime and synthetic acceptance suite.

This public release contains no private inventory or third-party site snapshot.
