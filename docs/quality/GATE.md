# Quality gate

Profile: private local workstation. Date: 2026-10-02. Decision: **REVISE**. This file does not call the gate a release pass.

Evidence routes: `http://127.0.0.1:3011` (production `next start` after the build) and the earlier Chrome walk against the dev server on the same origin. Screenshots are in this directory. The API is `http://127.0.0.1:8765`.

| ID | Result | Evidence |
|---|---|---|
| Q01 Production domain | N/A | No public release. The desk is loopback only. No domain was invented. |
| Q02 Page titles | PASS | Production `/login` title is `Sign in · RETRACE`. The ecology view title was `Ecology measurements · RETRACE`. The 404 heading is product copy, and the desk title template is `%s · RETRACE`. |
| Q03 Meta descriptions | PASS | Layout description is a product sentence with no project data. `robots` is `noindex`. Production login HTML contains that description and `noindex`. Unsigned project metadata falls back to the title `Project` when the API refuses the read. |
| Q04 Favicon | PASS | `/icon.svg` returned 200 `image/svg+xml` (357 bytes), an R mark on a dark square. The browser walk reported no broken icon request. |
| Q05 Open Graph image | N/A | Private local app. No public share card is published, and no production origin exists to point one at. |
| Q06 Canonical URL | N/A | No approved public origin. A canonical host was not invented. |
| Q07 Social previews | N/A | Same reason as Q05 and Q06. Private content was not made public to test a preview. |
| Q08 Custom 404 | PASS | Production `GET /not-a-page` returned 404 and the body contains "That page is not on this desk." The browser walk clicked "Return to the desk" and landed on the desk heading. |
| Q09 Loading | BLOCKED | `app/loading.tsx` renders "Opening the record…". Responses in the walk were fast, so that pending state was not seen. |
| Q10 Error messages | BLOCKED | API tests cover ambiguous local time (409), refused uploads, and cross-account reads. The browser walk did not submit an invalid form or disconnect the API, so those screens were not observed. |
| Q11 Headings | PASS | Login h1 "Sign in". Desk h1 "Recover the analysis without changing what it means." Ecology h1 "Ecology measurements". Settings h1 "Settings". 404 h1 "That page is not on this desk." |
| Q12 Alternative text | PASS | The brand mark is `aria-hidden`. Tabs, the display-name field, Continue, Sign out, and Save settings have accessible names. Keyboard login and roving tab focus were exercised. No informative image lacks a text equivalent. |
| Q13 Sitemap and indexing | N/A | Private local app. Pages send `noindex`. No sitemap is published. `robots.txt` is not used as access control. |
| Q14 Console | PASS | The viewport walk's failure list was empty after the intentional 404 document was excluded. That navigation is a real 404, and Chrome logs the failed document load. No other page error or failed asset was recorded on the exercised routes. |
| Q15 Debug output | PASS | No `console.log` in `apps/web`. The executor prints a failure line to stderr when a notebook fails. That line is the operator signal for a failed run. |
| Q16 Source maps | PASS | `productionBrowserSourceMaps` is false. The login document's 9 scripts include no `.map` URL. `.next/static` has 0 map files. Server maps remain on disk under `.next/server` and are not in the client static output. |
| Q17 JavaScript | BLOCKED | Measured, no budget to compare. Login scripts total 577,784 bytes across 9 files. Largest files: 229,150, 159,933, and 112,594 bytes. Client CSS file: 8,886 bytes. These numbers are the baseline. |
| Q18 Mobile layout | PASS | 390×844 and 768×1024 document overflow is 0 on the ecology Run tab in the production build, after the result table and the long run buttons were constrained to the panel. Evidence and Lineage wrap onto a second row (`docs/quality/mobile-project.png`). The repair button label wraps in full (`docs/quality/mobile-run.png`). The arrange field stacks above its button at 390px. |
| Q19 Spacing | PASS | The screens use the token scale in `apps/web/app/globals.css`: paper, ink, verdigris accent, serif display, 4/8/12/16/24px steps, one radius. Light desk and the Urdu shell were inspected. Dark theme was not screenshotted. |
| Q20 Controls | PASS | Keyboard sign-in, arrow and End keys on the stage tabs, Save settings, Sign out back to the sign-in heading, 404 recovery, and the ecology run labels all completed. Connectors do not present a dead "Connected" state. |

## Browser sizes

- Phone 390×844, tablet 768×1024, desktop 1440×900 and 1280×800.
- `docs/quality/viewport-walk.json` records the tab boxes and overflow.
- `docs/quality/desktop-ecology.png` is the left-to-right run view. `docs/quality/desktop-ecology-rtl.png` is the same project after Urdu direction was saved.
