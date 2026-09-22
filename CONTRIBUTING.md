# Contributing

Thanks for helping improve Local MOD Browser. Pull requests are welcome, but every
change is reviewed before it can merge into `main`.

## Before opening a pull request

Please open an Issue first for a large feature, a data-model change, a new source
adapter, or a behavior that could affect compatibility. Small fixes and documentation
improvements can go straight to a PR.

Keep the change focused and describe the user problem, the design choice, and the
evidence that supports it. A PR is easier to review when it contains one coherent
change instead of a mixture of refactors, formatting, and unrelated features.

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

### Review and merge policy

- `main` is protected. Contributor changes must arrive through a pull request;
  force-pushes and branch deletion are disabled.
- At least one approving review is required before merge.
- The repository owner reviews every PR; code owners are defined in
  [`.github/CODEOWNERS`](.github/CODEOWNERS).
- CI must pass, review conversations must be resolved, and stale approvals may be
  dismissed when new commits change the reviewed code.
- Maintainers may request changes, ask for a smaller scope, or close a PR that does
  not meet the privacy, licensing, security, or compatibility boundaries.
- Approval is not automatic: a passing CI run means the code is testable, not that it
  is accepted for release.

Please do not pressure reviewers to merge quickly. The project values a small,
auditable history and safe local-data handling over a high change count.
