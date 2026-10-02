# RETRACE

Source: https://github.com/FrankAsanteVanLaarhoven/retraceos

RETRACE is a public platform for scientists. A scientist keeps an untouched snapshot of a notebook, approves a result contract, reviews a proposed repair, reruns an admitted notebook, and receives a separate verdict for execution and for agreement with that contract.

Each display name is one scientist account. The session cookie is HttpOnly. Session tokens and tool keys are stored as SHA-256 hashes. Account responses are marked `no-store`. Sign-in and changes are rate limited in the running process. A scientist can download their record or delete the account. The release decision for this tree is still **REVISE**: there is no approved public host, no tested sandbox for notebooks outside the three demonstrations, no database row security, and no completed data-protection assessment. It is licensed Apache-2.0. The credited author is Frank Asante Van Laarhoven.

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

Open `http://127.0.0.1:3011`. Sign in with a display name. That name is the scientist account. There is no password in this build.

A public operator sets `RETRACE_ORIGINS` to the HTTPS origin of the desk and `RETRACE_COOKIE_SECURE=1` so the session cookie is marked Secure. This checkout does not set those, and it keeps listening on this computer.

## Deploy on Vercel

Import this repository as one Vercel project. `vercel.json` defines two services in that project. `web` is the Next.js desk in `apps/web`. `api` is the FastAPI application in `app.py`, which loads `retrace.hosted:app`. Requests to `/api/assistant` stay on the desk, so Talk can read `OPENROUTER_API_KEY` on the server. Other `/api` requests, and `/mcp`, go to the API. The desk calls the API through the service binding `RETRACE_API`. You do not set that binding yourself.

A `vercel.app` address is a preview. It is not an approved production domain. The release decision stays **REVISE**.

Set these environment variables on the project when you need them:

- `OPENROUTER_API_KEY`, if Talk should call OpenRouter. Without it, Talk says it needs configuration and does not invent a reply. The key stays on the server.
- `RETRACE_DATABASE_URL`, or `POSTGRES_URL`, when accounts must remain. Use a PostgreSQL URL. The application stores notebook bytes in that database. PostgreSQL row-level security is not claimed, and this software does not enable it.
- Leave the database URL unset and the API keeps SQLite under `/tmp`. Accounts and projects then last only until that instance stops. That is not a scientist archive.
- `RETRACE_ORIGINS`, when the desk is served from a hostname other than the Vercel deployment host. On Vercel, `VERCEL_URL`, `VERCEL_BRANCH_URL`, and `VERCEL_PROJECT_PRODUCTION_URL` are allowed. The session cookie is marked Secure when `VERCEL` is set, unless `RETRACE_COOKIE_SECURE=0`.

The Vercel Python runtime for this API is 3.12, from `.python-version`. The local virtualenv can stay on 3.11. A practice notebook is allowed 45 seconds inside the API. The function has to be allowed to run at least that long. If the platform stops it first, the run fails and is not reported as a result. The untouched ecology notebook fails on purpose until its repair is approved. An unknown notebook stays blocked. The workstation `gh` login is not inside the function, so GitHub stays unconfigured there until a scientist connects an account the function can use. Slack, Google, and Colab stay unconfigured without their own credentials. Notebooks are not sent to Colab, Slack, or OpenRouter.

The sidebar section How to use is a step-by-step explanation of every screen, written for someone who is not a programmer. The same text is in [docs/HOW_TO_USE.md](docs/HOW_TO_USE.md).

The three demonstration projects are ecology measurements, a trajectory distance, and an assay table. Their faults are injected and labelled. They are teaching fixtures, not recovered publications.

## Limits that are part of the design

- Only the three admitted demonstration snapshots may execute. Any other notebook is refused. No operating-system sandbox has been tested, so the runner does not fall back to executing an arbitrary upload on the host.
- The database on this computer is SQLite with application-enforced account separation. PostgreSQL row-level security is not claimed. On a Vercel preview, records remain when `RETRACE_DATABASE_URL` or `POSTGRES_URL` is set. The steps are under Deploy on Vercel.
- GitHub is operational when the workstation `gh` login is a person. Export writes a project to a repository that account can write, and refuses `FrankAsanteVanLaarhoven/RetraceOS`. Slack shares a title only after that person connects a workspace token. Google Calendar OAuth and Colab stay `NEEDS_CONFIGURATION`. A notebook can be downloaded and opened in the person's own Colab; notebooks are not sent to Colab to run. The calendar file can be imported into the person's own Google Calendar. Local tools can read the signed-in person's project names and questions. They cannot run a notebook. The desk does not show the tool address. A private client file is written under `data/mcp/` and is not committed.
- Repairs come from a deterministic diagnoser and are not sent to a model. Talk, on every page, calls OpenRouter when `OPENROUTER_API_KEY` is set on the desk server. On Vercel that name is an environment variable of the Next.js app. The key is read only on the server and is not placed in the browser. The usual conversation uses `anthropic/claude-sonnet-5.5`. Explaining a result uses `anthropic/claude-opus-5.5`. Drafting a record uses `anthropic/claude-haiku-4.5`. Speech uses `mistralai/voxtral-mini-tts-2603`. Hearing uses `openai/gpt-4o-mini-transcribe`. A voice is chosen by gender, tone, and country from the voices that model can speak. A missing combination is named as the closest voice. Notebooks and stored results are not included. The service does not store the conversation. Without the key, Talk says it needs configuration and does not invent a reply. The reply is not a reproduction result.
- English is the authored source language. The other 35 locales are interface drafts and remain `NOT_REVIEWED`. Choosing one changes the interface copy and, for Arabic, Hebrew, Persian, and Urdu, the writing direction. Project names, notebooks, and scientific records stay in their source language.
- Evidence export is a ZIP with a Workflow Run RO-Crate subset. It is not a certified full RO-Crate profile.

The quality record is `docs/quality/GATE.md`. The release record is `docs/evidence/RELEASE_DECISION.md`.
