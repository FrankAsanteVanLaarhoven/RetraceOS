# Specification reconciliation

Date: 2026-10-02.

## Archive

| Item | Result on this machine |
|---|---|
| `RETRACE_AI_Claude_Code_Blueprint.zip` | Absent from Downloads, Desktop, Documents, `/tmp`, and this repository |
| Expected SHA-256 from the integrity note | `1864898f9d815862072f640642fdc42c2bd34e5f62dd74f7da728e4b27a81070` |
| Hash recomputed here | Not done. The bytes are not present |
| Integrity note | `/Users/favl/Downloads/blueprint_integrity_check.json` |
| Note's own scope | 55 entries claimed, 54/54 content hashes, 70/70 structure checks, application tests `NOT_RUN_HERE` |

The integrity note is a record of a check performed somewhere else. It is not the archive, and it is not evidence that this application implements that package.

## Requirements R01–R32

The integrity note lists the identifiers R01 through R32. Their requirement sentences, acceptance tests, JSON Schemas, skills, and agent definitions were inside the missing archive. They are **unmapped**. This tree does not invent a parallel RX catalogue and does not add 32 and any other count together.

What this tree does implement is described by the tests in `tests/test_retrace.py` and by `docs/evidence/TEST_REPORT.md`. Those tests are evidence about this code. They are not a score against the missing R-statements.

## Urdu, deviation D4

The master-prompt prose lists Arabic, Hebrew, and Persian as right-to-left and omits Urdu. The integrity note's copy of the original locale entry already has `ur-PK` with `"direction": "rtl"`, `catalogue_status` `NOT_IMPLEMENTED`, and `linguistic_review` `NOT_REVIEWED`.

D4 is that prose omission against the locale manifest. It is not a defect in the original JSON, which was not available here to diff byte for byte.

This repository's `src/retrace/locales.json` uses the tag `ur`, not `ur-PK`, because the file was authored here rather than extracted from the archive. Direction is `rtl`. Catalogue status is `NOT_IMPLEMENTED`. Linguistic review is `NOT_REVIEWED`. The settings screen keeps the English sentences and sets the document direction from the catalogue. A browser check on 2026-10-02 set Urdu, observed `documentElement.dir === "rtl"`, placed the rail on the right, and kept the English paragraphs left to right.

## Contract authority

`src/retrace/uiplan.py` is the runtime authority for a UI plan. The prompt bar submits to that validator. Words that would approve, run, or invent a query are rejected. Panel names are the allowlist `brief`, `notebook`, `proposal`, `checks`, `lineage`, and `evidence`. There is no second schema file claiming to be the original draft, because those drafts were in the missing archive.
