# RETRACE

Source: https://github.com/FrankAsanteVanLaarhoven/retraceos

RETRACE is a local scientific evidence desk. A researcher imports a notebook, keeps an untouched snapshot, approves a result contract, reviews a proposed repair, reruns the admitted notebook, and receives a separate verdict for execution and for agreement with that contract.

The desk is a workstation prototype. The release decision for this tree is **REVISE**. It is licensed Apache-2.0. The credited author is Frank Asante Van Laarhoven.

## What a run can say

A finished run carries two statuses.

- Execution records whether the admitted notebook finished and wrote `outputs/results.json`.
- Verification records the independent comparison: `REPRODUCED_WITHIN_CONTRACT`, `EXECUTED_NOT_VERIFIED`, `CHANGED_RESULT`, `BLOCKED_MISSING_EVIDENCE`, `FAILED_EXECUTION`, or `NOT_RUN`.

Agreement with the declared checks is the stated numerical comparison. The desk states that this comparison does not establish the scientific conclusion.

The repair path cannot edit the contract, the reference outputs, or the verifier. An approval is bound to the candidate, the contract, and the snapshot. A later change invalidates it. A methodological edit, including a change of units, exclusions, or sample population, stays a reanalysis even when a number still matches.

## Run it on this machine

The API listens on `127.0.0.1:8765`. The desk listens on `127.0.0.1:3011`.

```bash
cd /Users/favl/workspace/retrace
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
.venv/bin/python -m ipykernel install --sys-prefix --name retrace
.venv/bin/python -m retrace.api
```

In a second shell:

```bash
cd /Users/favl/workspace/retrace/apps/web
pnpm install
pnpm dev
```

Open `http://127.0.0.1:3011`. Sign in with a display name. That name is the local account. This is not institutional sign-in.

The three demonstration projects are ecology measurements, a trajectory distance, and an assay table. Their faults are injected and labelled. They are teaching fixtures, not recovered publications.

## Limits that are part of the design

- Only the three admitted demonstration snapshots may execute. Any other notebook is refused. No operating-system sandbox has been tested, so the runner does not fall back to executing an arbitrary upload on the host.
- The database is SQLite with application-enforced account separation. PostgreSQL row-level security is not claimed.
- GitHub, Slack, Google Calendar, Colab, and a RETRACE MCP server are `NEEDS_CONFIGURATION`. Internal calendar events and ICS export work without Google.
- Repairs in this build come from a deterministic diagnoser. A model key present in the environment is reported as `CONFIGURED_NOT_USED` and is not called.
- English is the authored interface. Thirty-five other locales are catalogued, including Urdu as right to left, and remain `NOT_REVIEWED`. Choosing one changes writing direction and leaves the sentences in English.
- Evidence export is a ZIP with a Workflow Run RO-Crate subset. It is not a certified full RO-Crate profile.

The quality record is `docs/quality/GATE.md`. The release record is `docs/evidence/RELEASE_DECISION.md`.
