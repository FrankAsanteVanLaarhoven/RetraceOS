# Build report

Date: 2026-10-02. Path: `/Users/favl/workspace/retrace`. No git commit.

## What runs

- Python package `retrace` 0.1.0, src layout, script `retrace-api`.
- API: FastAPI on `127.0.0.1:8765`, SQLite, local object directory `data/objects`.
- Runner: a subprocess of the admitted notebook with the `retrace` kernel, a temporary workspace, a path jail, a stripped environment, a 45-second timeout, and a 64KB limit on `outputs/results.json`.
- Verifier: a separate function with no model authority. It never promotes a notebook's own grade.
- Web: Next.js 16.3.6 desk on `127.0.0.1:3011`, proxying `/api` to the local API. `devIndicators` is false, `poweredByHeader` is false, `productionBrowserSourceMaps` is false.

## What was deliberately left out

LangGraph, PostgreSQL, Redis, pgvector, a Claude repair agent, OpenRouter routing, OIDC, GitHub App installation, Slack, Google Calendar OAuth, Colab MCP, and translated copy for 35 locales. Each missing external service stays `NEEDS_CONFIGURATION` or is described as absent. None is simulated as healthy. A local tool connection can read the signed-in person's project names and questions. It cannot run a notebook, and the desk does not show its address.

## Production desk bundle

`pnpm exec next build` in `apps/web` completed on 2026-10-02 (Next.js 16.3.6, TypeScript check finished). The production server is `next start` on `http://127.0.0.1:3011`.

The login document referenced 9 JavaScript files totalling 577,784 bytes. None of those URLs is a source map. `.next/static` contains 0 `.map` files. `.next/server` contains server maps on disk; `productionBrowserSourceMaps` is false, and those files are not in the static client output. The built client CSS file is 8,886 bytes. No bundle budget had been recorded before this build, so the figures are a baseline rather than a pass against a limit.

## Package proof

Clean virtualenv `/tmp/retrace-clean`, Python 3.11.4. Wheel SHA-256 `c1ca1a02346811af15bc81e098bf69d06eb1b4cddea3342c88b85dcf89536ec6`. Import path is site-packages, recorded in `docs/evidence/TEST_REPORT.md`.
