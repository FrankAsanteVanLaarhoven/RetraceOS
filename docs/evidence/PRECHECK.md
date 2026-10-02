# Precheck

Recorded 2026-10-02 on this workstation. Eight fields.

## 1. Objective

Build a local RETRACE desk that can import an admitted notebook, preserve a snapshot, approve a result contract, review a repair, run that candidate apart from the verifier, and export an evidence bundle. The profile under test is `workstation-local`.

## 2. Repository and working tree

Path: `/Users/favl/workspace/retrace`. There is no git repository and no branch named `build/retrace-t0-t2` on this machine. No commit was created.

## 3. Source of truth and rights

The implementation in this directory is the source of truth for what runs. The master prompt is present at `/Users/favl/Downloads/RETRACE_AI_CLAUDE_CODE_MASTER_PROMPT.md`. The blueprint archive `RETRACE_AI_Claude_Code_Blueprint.zip` is not on this machine. A second-hand integrity note is at `/Users/favl/Downloads/blueprint_integrity_check.json`. It names SHA-256 `1864898f9d815862072f640642fdc42c2bd34e5f62dd74f7da728e4b27a81070` and states that its own check did not run the application. That hash was not recomputed here because the archive is absent.

Code written in this tree is Apache-2.0 and credited to Frank Asante Van Laarhoven. No university or company tree was copied in. RESEARCH_AI data, authentication files, and logs were not imported.

## 4. Installed tools

- Python 3.11.4 in `/tmp/retrace-clean` and the project `.venv`.
- Wheel `retrace-0.1.0-py3-none-any.whl`, SHA-256 `c1ca1a02346811af15bc81e098bf69d06eb1b4cddea3342c88b85dcf89536ec6`.
- FastAPI 0.142.2, Pydantic 2.13.5, SQLAlchemy 2.1.2, nbclient 0.11.0, pytest 9.1.1 in the clean environment.
- Node v25.5.0, pnpm 10.20.0, Next.js 16.3.6, React 19.2.8, TypeScript 5.9.2.
- Docker and PostgreSQL are not installed. `psql` is absent.
- Chrome was driven through playwright-core in `/tmp/retrace-browser`, which is not a product dependency.

## 5. Data classification and egress

Demonstration notebooks and their small CSV tables are labelled fixtures. Session data lives in `data/` on this workstation and is gitignored. The running API process can see an Anthropic key in its environment. Capabilities report that key as `CONFIGURED_NOT_USED`. This build does not call Anthropic or OpenRouter and does not send notebooks or results to a model provider. No remote push, deploy, or external message was sent. A later desk route, Talk, calls OpenRouter for a conversation when `OPENROUTER_API_KEY` is set on the Next.js server. Repairs still do not call a model, and notebooks are still not sent.

## 6. Authorised actions and budget

Local implementation, local tests, and a local browser walk were in scope. Paid model calls, publication, deployment, and remote git writes were not authorised and were not performed. No spend was recorded because no provider was called.

## 7. Acceptance tests and baseline health

The clean install imported `retrace` from `/private/tmp/retrace-clean/lib/python3.11/site-packages/retrace/__init__.py` with `PYTHONPATH` unset, working directory `/tmp`. Pytest collected 17 tests, printed 17 passing dots, and exited 0. Warnings: Starlette's deprecation of `httpx` with `starlette.testclient`, and nbformat's missing id on the deliberately untrusted notebook in `test_untrusted_notebook_is_not_executed`. See `docs/quality/pytest-installed.txt`.

The desk at `http://127.0.0.1:3011` completed sign-in, the ecology run view, sign-out, a 404 recovery, settings, and the connector page. See `docs/quality/GATE.md`.

## 8. Blockers and assumptions

- The original blueprint archive and the text of requirements R01–R32 are not on disk, so they are not mapped onto this code.
- The original threat labelled T10 is not on disk and is not quoted.
- PostgreSQL row-level security cannot be tested here.
- No sandbox boundary has been tested. Arbitrary execution stays closed.
- The human-participant effort study is `NOT_RUN`.
- Assumption: a display name is an acceptable local account for this prototype, and anyone who can open the port on the machine can choose one.
