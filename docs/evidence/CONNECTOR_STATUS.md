# Connector status

Observed from `GET /api/connectors`, a notebook download, and the connectors page in Chrome on 2026-10-02. The API was `http://127.0.0.1:8765`. The desk was `http://127.0.0.1:3011`.

These connections belong to the person using the desk. They are not a check of the RETRACE application repository.

| Connector | Status | What was checked |
|---|---|---|
| GitHub | OPERATIONAL | The workstation `gh` login is FrankAsanteVanLaarhoven. The card links to `https://github.com/FrankAsanteVanLaarhoven`. Export to `FrankAsanteVanLaarhoven/RetraceOS` was refused. The card says that repository is the application. |
| Slack | NEEDS_CONFIGURATION | No workspace token is saved for this person. Nothing is sent to Slack. The card asks for that person's token. |
| Google Calendar | NEEDS_CONFIGURATION | No Google sign-in. The card opens the desk calendar, downloads the calendar file, and opens Google Calendar so the file can be imported into that person's account. |
| Colab | NEEDS_CONFIGURATION | No Colab session. Download of the Assay table notebook returned `200` `application/x-ipynb+json` as `analysis.ipynb`. Notebooks are not sent to Colab to run. |
| RETRACE MCP | OPERATIONAL | The connectors page does not show an address or a copy control. A tool call for the signed-in desk account returned the project names Assay table, Trajectory length, and Ecology measurements. A request to run a notebook was refused. The private client file under `data/mcp/` is mode 0600 and is not returned by the API. |

A missing credential is not shown as Working. Creating a private repository was not clicked.
