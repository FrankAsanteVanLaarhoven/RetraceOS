# Connector status

Observed from `capabilities()` and from the connectors page in Chrome on 2026-10-02.

| Connector | Status | What works without it |
|---|---|---|
| GitHub | NEEDS_CONFIGURATION | Nothing is fetched from GitHub |
| Slack | NEEDS_CONFIGURATION | Nothing is sent to Slack |
| Google Calendar | NEEDS_CONFIGURATION | Internal events and ICS export are implemented. Ambiguous local times return 409 unless a fold is chosen. That 409 is an API test, not a browser click |
| Colab | NEEDS_CONFIGURATION | Not an execution backend |
| RETRACE MCP | NEEDS_CONFIGURATION | No MCP tool server is exposed |

The connectors page showed these states and did not display a Connected claim.
