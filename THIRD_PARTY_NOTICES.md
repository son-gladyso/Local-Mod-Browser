# Third-party notices

Local MOD Browser is licensed under the MIT License. That license applies only
to the project code and documentation for which the project contributors hold
the necessary rights.

## Pinned runtime components

The bootstrap tool downloads these components from their official publishers;
the binaries are not stored in this repository.

- CPython 3.13.15 — Python Software Foundation License 2.0. Source, archive
  checksum and license URL are recorded in `runtime-lock.json`.
- SQLite 3.53.4 — public-domain dedication/blessing. Source, archive checksum
  and notice URL are recorded in `runtime-lock.json`.

## Bundled font

- Inter (variable, Latin and Latin Extended subsets), Copyright 2016 The Inter
  Project Authors — SIL Open Font License 1.1. Files: `static/fonts/inter-*.woff2`,
  taken unmodified from the `@fontsource-variable/inter` 5.3.0 package; the
  license text is in `static/fonts/Inter-OFL.txt`.

The interface theme takes visual cues from the Nexus Mods website, but no Nexus
Mods styles, fonts, icons, images or other assets are included.

## Optional development dependencies

Packages listed in `requirements-test.txt`, `requirements-mcp.txt`,
`requirements-platform.lock` and `package.json` remain subject to their own
licenses. Installing them does not change this project's MIT license.

## User and third-party content

No license is granted for MOD archives, game assets, screenshots, author text,
Nexus Mods data, or other content imported by a user. This repository does not
ship those materials.
