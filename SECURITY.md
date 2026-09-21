# Security policy

## Supported version

Security fixes are applied to the latest release on the default branch.

## Reporting a vulnerability

Please use GitHub's private vulnerability reporting feature for this repository.
Do not open a public issue for a vulnerability that could expose local files,
tokens, databases or browser sessions.

Include the affected version, reproduction steps, expected impact and any safe
diagnostic output. Remove personal paths, MOD metadata and session tokens before
attaching logs.

## Security boundary

The service is designed to bind only to `127.0.0.1`. It is not intended to be
exposed to a LAN or the public internet. Runtime tokens, databases, backups and
exports are local secrets and are excluded from Git by default.
