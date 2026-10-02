# Threat model

Profile this document applies to: `workstation-local`, curated demonstrations, 2026-10-02.

The blueprint threat labelled T10 is not in the files on this machine. Its sentence is not quoted and is not treated as mitigated. The residual below is the one this architecture can state from its own code.

## Residual: a notebook can write internally consistent outputs

- Assets: `outputs/results.json`, the approved checks, the verification status shown to a reviewer.
- Actor: code inside an allowlisted demonstration notebook, or any later runner that executes untrusted notebooks.
- Capability: write numbers that satisfy the declared checks without having performed the analysis the prose describes.
- Mitigations present: the repair path cannot edit the contract, the reference, or the verifier; a method change cannot be relabelled as an execution repair; the notebook's own verification field is ignored; notebooks outside the three hashes are not started.
- Remaining exposure: an allowlisted notebook can still emit a matching `results.json`. The outcome copy says the comparison is not a scientific conclusion. That sentence does not detect a fabricated-but-consistent table.
- Release effect: acceptable only for the curated local demonstrations, where the fixtures are authored and labelled. It blocks any profile that executes uploads, repository snapshots, or third-party notebooks. No gVisor, virtual machine, or other sandbox was configured or tested. Absence of a sandbox refuses execution. It does not fall back to the host.

## Other boundaries that were implemented and tested

- Accounts are display names. One name cannot read another's project (`test_accounts_cannot_read_each_other`). This is application filtering on SQLite. It is not PostgreSQL row-level security, and a database file copied off the machine is not protected by that filter.
- Mutations require an allowed Origin. The session cookie is HttpOnly and SameSite=Lax. The stored token is a SHA-256 hash. Account responses use Cache-Control no-store. Sign-in is limited to 40 requests a minute per client address in the process, and other changes to 500. A scientist can download their record without session tokens or connector secrets, and can delete the account.
- Pickle uploads are refused. Paths must be relative. Dotfiles are refused.
- A changed patch after approval does not keep the old approval (`test_approval_dies_when_the_patch_changes`).
- A finished run cannot be cancelled into a different state. A repeated idempotency key returns the same run.
- A tampered evidence ZIP fails import.
- The prompt bar cannot approve a run or name a panel outside the allowlist.
- Talk sends the words of a turn, and a short recording when the scientist speaks, to OpenRouter only when the desk server has `OPENROUTER_API_KEY`. It does not send notebooks or stored results, and it does not store the conversation. It cannot approve a contract or assign a reproduction status. The microphone is allowed for this page only. Camera and location stay blocked.

## Boundaries that are not claimed

Institutional OIDC, MFA, tenant row-level security, secret-manager encryption, an independent penetration test, and an OWASP ASVS certification. See `docs/security/ASVS.md`.
