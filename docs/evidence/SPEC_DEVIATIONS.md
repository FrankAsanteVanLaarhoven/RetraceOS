# Specification deviations

## D4. Urdu in the prose and in the locale manifest

The master prompt's prose names Arabic, Hebrew, and Persian as right-to-left languages and does not name Urdu. The integrity note for the original locale manifest already contains:

```json
{
  "tag": "ur-PK",
  "language": "Urdu",
  "direction": "rtl",
  "catalogue_status": "NOT_IMPLEMENTED",
  "linguistic_review": "NOT_REVIEWED"
}
```

Kept behaviour: Urdu is right to left. Clarification, appended 2026-10-02: D4 is an omission in the prose relative to that manifest, not a defect in the original JSON.

Local tag: this tree uses `ur` because `src/retrace/locales.json` was written here. The original file was not extracted, so this tag is not presented as the archive's tag.

## Other differences from the master prompt, recorded because the archive was absent

- Persistence is SQLite. The prompt asks for PostgreSQL. No PostgreSQL server is installed, so row-level security is not claimed.
- Workflow state is the application service in-process. LangGraph is not a dependency of this tree.
- The repair proposer is a deterministic diagnoser over the three fixtures. A Claude repair worker is not wired, so a missing model call cannot be shown as a successful repair.
- Connectors report `NEEDS_CONFIGURATION`. They do not simulate an installation.
- Locales other than English have no translated interface copy.
