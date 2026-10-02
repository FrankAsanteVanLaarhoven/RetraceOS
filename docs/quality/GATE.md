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

## Follow-up: account menu and locale drafts

Date: 2026-10-02. Dev server `http://127.0.0.1:3011`, API `http://127.0.0.1:8765`. Chrome via playwright-core. This does not replace the table above and does not call the gate a release pass. Decision remains **REVISE**.

| ID | Result | Evidence |
|---|---|---|
| Q02 Page titles | PASS | Observed `Desk · RETRACE`, `Bureau · RETRACE`, `میز · RETRACE`, `Stół · RETRACE`, and `Sign in · RETRACE`. |
| Q12 Alternative text | PASS | The theme control is named "Switch to dark theme" or "Switch to light theme". The account control exposes the display name and "Local session". Icons are `aria-hidden`. |
| Q14 Console | PASS | The mobile menu and sign-out run, and the later Polish and Persian run, recorded no app-owned console errors. An earlier run showed a 401 from preferences on the login page and a 500 from sign-out; the proxy now returns 204 with an empty body, and an unsigned preferences read returns 200 with `signed_in: false`. |
| Q15 Debug output | PASS | No `console.log` in `apps/web`. |
| Q18 Mobile | PASS | At 390×844, document overflow was 0 on the connectors view, the open account menu, the closed rail, and the login page. The menu box was x=12, right=378, and the Theme label started at x=29. Hide and Show changed the rail. |
| Q19 Spacing | PASS | The menu uses the existing paper, line, radius, and 12px page inset. |
| Q20 Controls | PASS | The theme toggle persisted `dark` across reload and returned to light. The name menu held theme, density, language, clock zone, and Sign out. No separate Sign out remained in the bar. Escape closed the menu and returned focus. Dutch, Urdu, Polish, and Persian changed the interface. Connectors still say they need configuration. |
| Q09 Loading | BLOCKED | Not exercised with a slowed response in this pass. |
| Q10 Errors | BLOCKED | API test rejects locale `xx` with 400 `bad_locale`. The browser pass did not submit an invalid time zone. |
| Q17 JavaScript | BLOCKED | Not remeasured. Locale catalogues load on demand and are not in the English bundle. No budget is recorded. |

## Follow-up: clock and guide

Date: 2026-10-02. Dev server `http://127.0.0.1:3011`, API `http://127.0.0.1:8765`. Chrome via playwright-core, signed in as the existing local display name. This does not replace the tables above and does not call the gate a release pass. Decision remains **REVISE**.

| ID | Result | Evidence |
|---|---|---|
| Q02 Page titles | PASS | The guide view title was `Guide · RETRACE`. |
| Q11 Heading structure | PASS | One `h1`, “How to use this desk”. The contents links move to the matching `h2`. |
| Q12 Alternative text | N/A | This page adds no informative image and no new icon-only control. |
| Q14 Console | PASS | The guide walk recorded no app-owned console errors. |
| Q18 Mobile layout | PASS | Desktop 1440×900, tablet 768×1024 overflow 0, phone 390×844 overflow 0. The UTC clock was one line. Screenshots: `docs/quality/guide-desktop.png`, `docs/quality/guide-mobile.png`. |
| Q19 Spacing | PASS | The guide uses the existing space scale, a 68ch measure, and the same paper and type as the desk. |
| Q20 Controls | PASS | Sidebar Guide was the current page. “Read the step-by-step guide” and the contents link “Open a practice case” both opened the right place. Clock zone `Europe/London` showed `22:02 Europe/London` over `21:02 UTC` (`docs/quality/guide-london.png`), then `UTC` showed one line again. Escape returned focus to the name button. Saved theme stayed light. |
| Q09 Loading | BLOCKED | The clock has a loading line, but this pass did not slow the response. |
| Q10 Errors | BLOCKED | This pass did not submit an invalid time zone in the browser. |
| Q17 JavaScript | BLOCKED | Not remeasured. No budget is recorded. |

## Follow-up: how-to in the sidebar

Date: 2026-10-02. Dev server `http://127.0.0.1:3011`. Chrome via playwright-core. This does not replace the tables above and does not call the gate a release pass. Decision remains **REVISE**.

| ID | Result | Evidence |
|---|---|---|
| Q02 Page titles | PASS | The how-to view title was `How to use · RETRACE`. |
| Q11 Heading structure | PASS | One `h1`, “How to use this desk”. The sidebar section uses the same `h2` pattern as Projects. |
| Q14 Console | PASS | The sidebar walk recorded no app-owned console errors. |
| Q18 Mobile layout | PASS | At 1440×900 the rail scrolls inside the viewport. At 390×844, document overflow was 0. Screenshot: `docs/quality/sidebar-guide-desktop.png`. |
| Q20 Controls | PASS | Sidebar “Open a practice case” opened that section and was marked current. The project link for Ecology measurements could be scrolled into the rail. The clock stayed one UTC line. |
| Q09 Loading | BLOCKED | Not exercised with a slowed response. |
| Q10 Errors | BLOCKED | No invalid time zone was submitted. |
| Q17 JavaScript | BLOCKED | Not remeasured. |

## Follow-up: connector checks

Date: 2026-10-02. Dev server `http://127.0.0.1:3011`, API `http://127.0.0.1:8765`. Chrome via playwright-core. This does not replace the tables above and does not call the gate a release pass. Decision remains **REVISE**.

| ID | Result | Evidence |
|---|---|---|
| Q02 Page titles | PASS | The connectors view title was `Connectors · RETRACE`. |
| Q10 Errors | PASS for this flow | Slack, Google Calendar, and Colab stay Needs configuration and say what is missing. A request to run a notebook through MCP returned an error and did not run. |
| Q14 Console | PASS | The connector walk recorded no app-owned console errors. |
| Q18 Mobile layout | PASS | At 390×844, document overflow was 0. |
| Q20 Controls | PASS | GitHub and MCP showed Working. Open the desk calendar opened Calendar. The calendar file download returned `BEGIN:VCALENDAR`. Screenshot: `docs/quality/connectors-desktop.png`. |
| Q09 Loading | BLOCKED | Not exercised with a slowed response. |
| Q17 JavaScript | BLOCKED | Not remeasured. |

## Follow-up: favicon

Date: 2026-10-02. Dev server `http://127.0.0.1:3011`. Chrome via playwright-core. This does not replace the tables above and does not call the gate a release pass. Decision remains **REVISE**.

The navbar mark is unchanged (28px, stroke 1.7). The same rounded tile and cream R is now the favicon, with stroke 2.4 so the letter still reads at tab size.

| ID | Result | Evidence |
|---|---|---|
| Q04 Favicon | PASS | Login HTML links `/favicon.ico` (16, 32, and 48), `/icon.svg`, and `/apple-icon.png` (180). All three returned 200. The ICO directory holds three 32-bit frames. Chrome decoded the SVG and the Apple PNG on the sign-in page. A tab-sized rendering of each file shows the dark rounded tile and the cream R. Screenshot: `docs/quality/favicon-sheet.png`. |
| Q14 Console | PASS | The sign-in walk recorded no app-owned console errors. |
| Q18 Mobile layout | PASS | Sign-in at 390×844 kept document overflow at 0 and the title `Sign in · RETRACE`. |
| Q09 Loading | BLOCKED | Not exercised with a slowed response. |
| Q17 JavaScript | BLOCKED | Not remeasured. |

## Follow-up: own-account connectors

Date: 2026-10-02. Dev server `http://127.0.0.1:3011`, API `http://127.0.0.1:8765`. Chrome via playwright-core. This does not replace the tables above and does not call the gate a release pass. Decision remains **REVISE**.

| ID | Result | Evidence |
|---|---|---|
| Q02 Page titles | PASS | The connectors view title was `Connectors · RETRACE`. |
| Q10 Errors | PASS for this flow | Export to `FrankAsanteVanLaarhoven/RetraceOS` returned the message that the repository is the RETRACE application, and the next step to type a repository on the person's own account. Slack, Google, and Colab stay Needs configuration and say what is still missing. |
| Q14 Console | PASS | The only console error on that walk was the 400 from the refused application-repository export. The card showed the message. |
| Q18 Mobile layout | PASS | At 390×844, document overflow was 0. The export control was visible. Screenshot: `docs/quality/connectors-own-mobile.png`. |
| Q20 Controls | PASS | GitHub showed the signed-in account FrankAsanteVanLaarhoven and opened that account, not the application repository. The Assay table notebook downloaded as `analysis.ipynb`. Slack offered a token field. The calendar file and Google Calendar links were present. Copy changed the MCP button to Copied. Screenshot: `docs/quality/connectors-own-desktop.png`. |
| Q09 Loading | BLOCKED | Not exercised with a slowed response. |
| Q17 JavaScript | BLOCKED | Not remeasured. |

## Follow-up: MCP reads the desk

Date: 2026-10-02. Dev server `http://127.0.0.1:3011`, API `http://127.0.0.1:8765`. Chrome via playwright-core, signed in as the existing local display name. This does not replace the tables above and does not call the gate a release pass. Decision remains **REVISE**.

The connectors card no longer shows an address or a copy control. A tool call for that desk account returned the project names Assay table, Trajectory length, and Ecology measurements. A request to run a notebook was refused and did not run.

| ID | Result | Evidence |
|---|---|---|
| Q02 Page titles | PASS | The connectors view title was `Connectors · RETRACE`. |
| Q10 Errors | PASS for this flow | A tool that is not a read returned the message that the tool is not available and that this connection cannot run a notebook or send work to Colab. |
| Q11 Headings | PASS | The page heading is Connectors. MCP is the heading of its card. |
| Q14 Console | PASS | The connectors walk recorded no app-owned console errors. |
| Q18 Mobile layout | PASS | At 390×844, document overflow was 0. The card lists the three reads. Screenshot: `docs/quality/mcp-card-mobile.png`. |
| Q19 Spacing | PASS | The card uses the existing card, status, and list spacing. Screenshot: `docs/quality/mcp-card-desktop.png`. |
| Q20 Controls | PASS | The address field count was 0 and the Copy button count was 0. The card states the three reads and that a notebook cannot be run. |
| Q09 Loading | BLOCKED | Not exercised with a slowed response. |
| Q17 JavaScript | BLOCKED | Not remeasured. |

## Follow-up: How to use collapses

Date: 2026-10-02. Dev server `http://127.0.0.1:3011`. Chrome via playwright-core, signed in as the existing local display name. This does not replace the tables above and does not call the gate a release pass. Decision remains **REVISE**.

How to use starts closed. Choosing it opens the fifteen section lines. Choosing it again, including with Enter, closes them. The choice stays after a reload. Projects stay listed while the section is closed.

| ID | Result | Evidence |
|---|---|---|
| Q02 Page titles | PASS | After Open a practice case, the view title was `How to use · RETRACE`. |
| Q11 Headings | PASS | How to use remains a sidebar `h2`. The desk page heading stayed the page title. |
| Q14 Console | PASS | The collapse walk recorded no app-owned console errors. |
| Q18 Mobile layout | PASS | At 1440×900 the closed section left Projects in the rail. At 768×1024 and 390×844, document overflow was 0 with the list closed and with it open. Screenshots: `docs/quality/guide-collapse-desktop.png`, `docs/quality/guide-collapse-mobile.png`. |
| Q19 Spacing | PASS | The control uses the existing rail heading size, the 36px control height, and the paper hover. Screenshot: `docs/quality/guide-open-mobile.png`. |
| Q20 Controls | PASS | The closed list did not show Start here. Enter opened it. Open a practice case opened `#case` and was marked current. The last line was If something goes wrong. Reload kept the section open. |
| Q09 Loading | BLOCKED | Not exercised with a slowed response. |
| Q17 JavaScript | BLOCKED | Not remeasured. |
