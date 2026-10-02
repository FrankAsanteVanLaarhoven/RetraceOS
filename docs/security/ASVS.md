# ASVS applicability

This is a readiness note for the `workstation-local` prototype. It is not an OWASP ASVS certification, not a scored level, and not a pentest.

| Area | What exists in this tree | What was not done |
|---|---|---|
| Session | HttpOnly SameSite=Lax cookie, hashed token, scientist display-name account. Secure is set when `RETRACE_COOKIE_SECURE=1` | OIDC, MFA, passkeys, institutional recovery |
| Access control | Application queries filtered by account; cross-account test passed | PostgreSQL RLS, a non-owner role, a pooled `SET LOCAL` identity |
| Input | Upload suffix, size, path, and pickle checks; UIPlan allowlist | A reviewed malware corpus, macro stripping for Office formats |
| Execution | Allowlist plus refusal of everything else | A tested sandbox, hostile-notebook execution, resource-limit measurement beyond the runner's own timeout and `RLIMIT` |
| Cryptography | SHA-256 for content identity and session-token storage | No custom cipher. No managed key store |
| Logging | Executor failures go to stderr with the exception type | No structured redaction audit, no signed log sink |
| Privacy | Public notice, record download, and account deletion. Account responses use `no-store`. Sign-in and changes are limited per machine address in the process | No completed data-protection assessment, no processor register, no retention job, no encrypted database |

A passing fixture test is not evidence that the corresponding ASVS item is satisfied.
