# Public Demo Walkthrough

This walkthrough documents a reproducible, privacy-safe public demonstration. It
uses the eight fictional records in [`examples/demo-game/catalog-data.json`](../examples/demo-game/catalog-data.json).
No private inventory, MOD archive, game asset, or third-party site snapshot is used.

## What the demo proves

1. The browser starts with a local source and reports one demo game.
2. The catalog displays eight records with fictional authors, tags, dates, and counts.
3. The filter bar can narrow the catalog by keyword; searching `Visual` returns the
   two fictional visual records.
4. A card opens a detail panel without leaving the browsing context.
5. The same layout remains usable at a narrow 390px viewport.
6. The local API, CLI, contract audit, collaboration test, and short soak test can
   be run without a remote account or real MOD content.

## Reproduce it locally

```powershell
New-Item -ItemType Directory -Force data | Out-Null
Copy-Item config\sources.example.json data\sources.json
python tools\bootstrap_runtime.py
.\.runtime\python.exe -X utf8 launcher.py --no-browser
```

Open the printed local URL, select **Demo Game**, search for `Visual`, and open any
card's full details. The screenshots in this folder were captured from that exact
flow with the public build.

## Evidence and boundaries

- Demo catalog size: 8 fictional records.
- Search example: `Visual` → 2 matching records.
- No archives or executable paths are shipped.
- The screenshots are product evidence, not a claim about any third-party catalog.
- Release verification remains available through the `SHA256SUMS.txt` asset in
  [v2.5.2](https://github.com/son-gladyso/Local-Mod-Browser/releases/tag/v2.5.2).
