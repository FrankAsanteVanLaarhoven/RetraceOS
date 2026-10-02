# Internationalisation status

`src/retrace/locales.json` lists 36 locales. English is the only authored and reviewed interface language. The other 35 are interface drafts: choosing one changes the desk copy, and Arabic, Hebrew, Persian, and Urdu also set `dir=rtl`. None of those 35 has had linguistic review. The catalogue marks them `INTERFACE_DRAFT` and `NOT_REVIEWED`.

Project names, notebook cells, result numbers, fixture questions stored on a project, and other scientific records stay in their source language. A missing message falls back to English. The account menu says so when the chosen language is not English.

| Locale | Direction | Catalogue | Linguistic review |
|---|---|---|---|
| en | ltr | INTERFACE_AUTHORED | SOURCE_LANGUAGE |
| ar, he, fa, ur | rtl | INTERFACE_DRAFT | NOT_REVIEWED |
| The other 31 | ltr | INTERFACE_DRAFT | NOT_REVIEWED |

Urdu's tag in this file is `ur`. The missing archive's manifest used `ur-PK`, according to the integrity note. See `docs/evidence/SPEC_DEVIATIONS.md`. That historical note describes the earlier direction-only behaviour. It is not the current desk.

Browser checks on 2026-10-02 chose Dutch and saw Dutch chrome with `dir=ltr`, then Urdu and saw Urdu chrome with `dir=rtl` and the primary heading running right to left. Stored project names stayed in their source language. A later check the same day opened Polish (`dir=ltr`) and Persian (`dir=rtl`) and then restored English. No non-English locale is a supported, reviewed translation.

The clock stores times in UTC. The ambiguous-time API test uses `America/New_York` at `2026-11-01T01:30` and expects 409 unless fold is 0 or 1.
