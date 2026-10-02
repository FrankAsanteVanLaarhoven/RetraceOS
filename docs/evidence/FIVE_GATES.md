# Five gates

Checkpoint 2026-10-02. Decision: **REVISE** for `workstation-local`. Detail is in `docs/evidence/RELEASE_DECISION.md`.

1. Specification reconciliation: **BLOCKED**. Archive absent. R01–R32 unmapped. Urdu RTL kept. D4 clarified as a prose omission.
2. Installed package: **PASS**. Site-packages import, 17 tests, exit 0.
3. Contract tests: **PASS** inside that same pytest run.
4. Scientific workflow: **PASS** on three fixture families, including rejection and missing evidence. Comparative study **NOT_RUN**.
5. Browser: **PASS** for sign-in, ecology verdicts, sign-out, 404, Urdu direction, and phone/tablet overflow. Loading and several error screens were not observed in the browser. See the quality gate.
