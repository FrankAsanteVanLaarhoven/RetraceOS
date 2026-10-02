# Release decision

**REVISE.** Profile: `workstation-local`. Date: 2026-10-02.

This is not a GO-PRODUCTION decision. A public hosted service, an institutional deployment, and any service that executes uploaded notebooks are out of scope until the blockers below have evidence.

## Five gates

| Gate | Outcome | Evidence |
|---|---|---|
| Specification reconciliation | BLOCKED | The blueprint ZIP is not on disk. R01–R32 sentences are unmapped. `docs/evidence/SPEC_RECONCILIATION.md` |
| Installed-package smoke test | PASS | Clean wheel import and 17 tests, exit 0, `PYTHONPATH` unset. `docs/evidence/TEST_REPORT.md` |
| Executable contract tests | PASS | UIPlan rejection, approval invalidation, hidden contract override, and the verifier tests in the same run |
| Scientific workflow | PASS on fixtures | Valid repair, result-changing repair, and missing evidence for three families. Browser showed both ecology verdicts. `docs/science/INITIAL_RESULTS.md` |
| Browser integration | PASS for the exercised journey | Sign-in, ecology run labels, sign-out, 404, settings, connectors, 390px and 768px. `docs/quality/GATE.md` |

The scientific gate passes for authored fixtures. It does not pass a generalisation claim. The reconciliation gate stays blocked, so the specification package and this code are not declared equivalent.

## Before a stronger decision

- Recover the blueprint archive and map R01–R32 to tests, or explicitly retire those identifiers.
- Run PostgreSQL row-level security tests on a disposable server.
- Test an execution sandbox, then decide whether any notebook outside the allowlist may run.
- Complete the human-participant study before quoting a time saving.
- Obtain linguistic review before calling a non-English locale supported.
- Produce a release SBOM from the artefacts that would actually ship, separate from the developer environment freeze.
