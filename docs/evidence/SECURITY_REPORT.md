# Security report

Date: 2026-10-02. Profile: `workstation-local`.

The controls that have executable tests are listed in `docs/security/THREAT_MODEL.md` and `docs/evidence/TEST_REPORT.md`. The ASVS note is `docs/security/ASVS.md`. It is not a certification.

No independent security review was commissioned. No production migration was applied. The local SQLite file `data/retrace.sqlite` holds the desk sessions created during the browser walk.

The environment inventory `docs/evidence/environment-python-clean.txt` is the `pip freeze` of `/tmp/retrace-clean` after installing the wheel plus pytest and httpx. It is an environment inventory of 62 distributions, including test tools. It is not a release SBOM for a backend, frontend, or runner artefact. The web lockfile is `apps/web/pnpm-lock.yaml`.

A configured Anthropic key in the API process environment is reported as `CONFIGURED_NOT_USED`. This report does not record the key. Talk reads `OPENROUTER_API_KEY` on the desk server only. The key is not written into the client bundle and is not recorded here.
