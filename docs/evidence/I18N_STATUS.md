# Internationalisation status

`src/retrace/locales.json` lists 36 locales.

| Locale | Direction | Catalogue | Linguistic review | Interface copy |
|---|---|---|---|---|
| en | ltr | INTERFACE_AUTHORED | SOURCE_LANGUAGE | Authored English |
| ar, he, fa, ur | rtl | NOT_IMPLEMENTED | NOT_REVIEWED | English sentences, document direction rtl |
| The other 31 | ltr | NOT_IMPLEMENTED | NOT_REVIEWED | English sentences |

Urdu's tag in this file is `ur`. The missing archive's manifest used `ur-PK`, according to the integrity note. See `docs/evidence/SPEC_DEVIATIONS.md`.

A browser check selected Urdu, saved settings, and observed `dir=rtl` with English copy isolated left to right. No locale other than English has had human linguistic review. None of them is labelled fully supported.

The clock stores and displays UTC in the screenshots taken on 2026-10-02. The ambiguous-time API test uses `America/New_York` at `2026-11-01T01:30` and expects 409 unless fold is 0 or 1.
