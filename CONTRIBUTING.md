# Contributing

Thanks for helping improve Local MOD Browser.

## Development setup

The supported development host is Windows 10/11 x64.

```powershell
python tools\bootstrap_runtime.py
python -m pip install -r requirements-test.txt
npm install
```

Use only synthetic or explicitly licensed fixtures. Never commit personal MOD
inventories, service tokens, local databases, archives, screenshots containing
private data, or third-party site snapshots.

## Required checks

```powershell
.\.runtime\python.exe -X utf8 -m unittest discover -s tests -v
python -X utf8 tests\contract_audit.py --fixture
node --check static/app.js
node --check static/editor.js
node --check tests/browser.cjs
git diff --check
```

Changes to UI behavior should also run the Playwright browser acceptance tests.
Changes to migrations, recovery, scheduling, batching or durability need focused
failure-path tests and an explanation of the evidence in the pull request.

## Pull requests

- Keep changes focused and explain user-visible behavior.
- Add or update tests for behavior changes.
- Update contracts, CLI, schemas and documentation together.
- Do not weaken SQLite durability settings to improve benchmark numbers.
- Confirm that `git status --ignored` contains no material that belongs in Git.
