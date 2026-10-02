"""Vercel entrypoint. Tests do not import this module, so import does not open the workstation database."""

from retrace.api import default_app

app = default_app()
