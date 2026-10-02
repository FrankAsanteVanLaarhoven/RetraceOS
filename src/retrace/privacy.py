"""Public privacy notice for a RETRACE service. This is not a completed data-protection assessment."""

from __future__ import annotations


def privacy_notice() -> dict:
    return {
        "product": "RETRACE",
        "audience": "RETRACE is a public platform for scientists. Each display name is one scientist account.",
        "cookie": {
            "name": "retrace_session",
            "purpose": "Remember which scientist is signed in.",
            "duration": "12 hours",
            "flags": "HttpOnly and SameSite=Lax. Secure is added when the operator serves the platform over HTTPS.",
            "tracking": "The session cookie is not an advertising cookie, and there is no tracking cookie.",
        },
        "stored": [
            "The display name",
            "Theme, density, language, and clock zone",
            "Projects, questions, notebooks, approvals, runs, records, and calendar times created on this service",
            "A SHA-256 hash of the session token",
            "A SHA-256 hash of the tool key for this account",
            "A Slack token only when that scientist pastes one",
        ],
        "not_done": [
            "Records are not sold",
            "Notebook files and stored results are not sent to a model provider",
            "A conversation turn is sent to OpenRouter only when the scientist uses the assistant and the server key is set. The service does not store that conversation. The reply is not a reproduction result.",
            "There is no password and no organisation sign-in in this build",
        ],
        "rights": {
            "export": "Settings downloads the record for the signed-in scientist. Session tokens and connector secrets are left out.",
            "erasure": "Settings can delete that account. Deletion removes the projects, sessions, and saved tokens from this service.",
            "sign_out": "Sign out ends the current session and keeps the record.",
        },
        "cache": "Responses that carry an account are marked no-store, so a shared cache does not keep them.",
        "hashing": "Session tokens and tool keys are stored as SHA-256 hashes. A notebook is identified by a SHA-256 hash.",
        "rate_limit": "Sign-in and changes are limited per machine address inside the running process. The count clears when that process restarts.",
        "separation": "One scientist cannot read another scientist's projects through the platform. The database file itself is not encrypted.",
        "controller": "The operator of the service that runs RETRACE is responsible for the records on that machine. This software does not name a hosting company.",
        "assessment": "A completed data-protection assessment is not part of this build.",
    }
