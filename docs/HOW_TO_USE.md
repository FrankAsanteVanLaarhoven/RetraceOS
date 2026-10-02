# How to use this desk

RETRACE is a local desk for looking at a computational analysis, keeping the original notebook, and checking a result against a contract you approved. This page walks through every part of the screen in order.

The steps below are in English, the reviewed language of this desk, so they stay exact. In the browser, open How to use in the sidebar. The address on this computer is `http://127.0.0.1:3011`.

## What this desk is for

Use RETRACE when you want to recover an analysis and still be able to say what changed.

1. Keep an untouched copy of the notebook. That copy is the snapshot.
2. Write down the result you are willing to accept. That is the contract. Approve it before you treat a run as a check.
3. Look at a proposed change. A small repair of the run is a different decision from a change of method.
4. Run the original, and later run only the exact change you approved.
5. Download a bundle another person can inspect. They still have to run it themselves.

## What it will not claim

- A number that matches the contract is a numerical check. It does not prove that a scientific conclusion is correct.
- Only three practice notebooks can run. Any other notebook can be opened and read. It will not run, because no tested sandbox is set up.
- GitHub is working when this computer is signed in to a GitHub account. Export sends a project to a repository that account can write. It does not use the RETRACE application repository. Slack shares a project title only after you connect your own workspace. Google Calendar is not signed in; download the calendar file and import it into your own calendar. Colab stays unset, and notebooks are not sent there to run. Download a notebook and open it in your own Colab. Tools on this computer can read your project names and questions. They cannot run a notebook.
- The desk stores its own calendar. It does not talk to Google Calendar.
- Repairs are not sent to a model. Talk, on every page, calls OpenRouter when the desk server has OPENROUTER_API_KEY. The usual conversation uses Anthropic Claude Sonnet. Explaining a result uses Claude Opus. Drafting a record uses Claude Haiku. You can speak or type, and the reply can be spoken in a voice chosen by gender, tone, and country. The service does not store that conversation, and it does not send notebooks or stored results. Talk cannot approve a contract or assign a reproduction result. A missing key leaves Talk unconfigured.
- The database is a local file on this workstation. It is not an institutional database with row-level security.
- A Vercel deployment serves the same desk over HTTPS. Set OPENROUTER_API_KEY for Talk. Set RETRACE_DATABASE_URL to a PostgreSQL URL if accounts must remain after the host restarts. Row-level security is not claimed. A vercel.app address is a preview.
- English is the reviewed language. Other languages change the buttons and headings. They are drafts, and the screen says so. Project names, notebook text, and stored results stay in the language they were written in.

## Sign in

1. RETRACE is a public platform for scientists. On this computer the address is `http://127.0.0.1:3011`.
2. Type the name that should appear on your record. Choose Continue. Privacy and your record says what is stored.
3. There is no password in this build. Each name is a separate scientist account. The session cookie is named `retrace_session`. It is HttpOnly, lasts 12 hours, and is not an advertising cookie.
4. Settings can download your record or delete the account. Deletion removes the projects, the session, and any saved token from this service.

## Find your way around

After you sign in, the screen has three areas.

### Top bar

- The RETRACE mark on the left returns you to the desk.
- The clock shows the time. If your clock zone is UTC, you see that time once. If you choose another zone, your zone is on the first line and UTC is on the second line.
- The round button switches between a light page and a dark page.
- Your name opens your personal settings. Sign out is inside that menu.

### Sidebar

1. Desk is the home page, with the three practice cases.
2. How to use, in this sidebar, opens and closes this list. Each line opens one section of this page.
3. Record drafts a project page from the files already on the desk.
4. Calendar stores review times on this workstation.
5. Connectors shows outside services. They are not connected.
6. Settings describes this workstation.
7. Projects lists the cases you have opened. The names stay as they were stored.

Choose Hide to slide the sidebar away. Move the pointer to the edge control to peek at it. Choose Show to pin it open again. On a phone, Hide becomes a small corner button.

### Main area

The page you chose fills the rest of the screen. The large heading is the title of that page.

## Theme, language, clock, and sign out

1. Choose the round button in the top bar. A moon switches to the dark page. A sun switches to the light page. The choice remains after you reload.
2. Choose your name. A menu opens.
3. Theme can follow the computer, stay light, or stay dark.
4. Density can be comfortable or compact. Compact fits more on the screen.
5. Language changes the interface. English is the reviewed text. Any other language is a draft, and the menu says that.
6. Clock time zone is a name such as `UTC` or `Europe/London`. Leave the field to save it. If the name is not recognised, the menu tells you what to type instead.
7. Choose Sign out. You return to the sign-in page. Your projects stay on this computer under the name you used.
8. Press Escape, or click outside the menu, to close it without signing out.

The same four settings are also on the Settings page.

## Open a practice case

The desk opens with three labelled demonstrations. The faults in them were put there on purpose, so you can see how the desk treats them.

1. Ecology measurements. A file path from another computer, a mean mass in grams, and a trap that drops a record.
2. Trajectory length. A missing file name, a length that must stay in metres, and a trap that leaves centimetres in place.
3. Assay table. A table separated by semicolons, a mean of every sample, and a trap that adds an exclusion.

Choose Open this case on a card. The project opens. If you have opened it before, it is also listed under Already on this desk and in the sidebar.

## Work through a project

A project has six stages. Use them in this order. The row of buttons under the title switches stage. You can also use the left and right arrow keys when a stage button is focused.

### 1. Snapshot

Read the untouched notebook. The long code under it is the notebook’s fingerprint. If the file changes, that code changes too. On a practice case, the desk says only that demonstration is allowed to run.

### 2. Contract

A contract says what result you will accept: who is included, what is excluded, the output, the expected value, and the unit. Choose Approve this contract. After that, a repair cannot edit the contract. If no contract is approved, nothing can be called reproduced.

### 3. Review

Read the proposed change. Removed lines and inserted lines are shown separately.

- An execution repair tries to make the same method run.
- A methodological reanalysis changes the method, such as the unit, the exclusions, or who is counted. It stays a reanalysis even if a number still matches.

Choose the contract this change is judged against, then approve the repair or approve it as a reanalysis. Approving a reanalysis does not produce a reproduced status. You need an approved contract before you can approve the change.

### 4. Run

1. Choose Run the untouched snapshot. That is the original, before any repair.
2. After a repair is approved, choose Run on that exact approved candidate.
3. Read the execution line, then each check: expected, actual, and whether it passed.

A package that is not a practice case can be inspected. The Run button will not start it.

### 5. Evidence

Finish a run first. Then choose the bundle link. The file contains the snapshot, the change, the contract, and a claimed status. Another account has to run it again. The claimed status is not a verification on their desk. Agreement with the contract is still not proof that the scientific conclusion is correct.

### 6. Lineage

The table shows where each relationship came from and where it goes. Observed means a check finished. Proposed means the change has only been suggested.

### The side panel and the arrangement

The panel on the right describes the contract or repair you select. It also repeats the limit: a matching number does not establish the conclusion.

The arrange field under the title can reorder the panels. It cannot approve a repair or start a run. Open Arrange panels if you want to drag a row, move it with the buttons, undo, or save the arrangement. Saving the arrangement does not hide the status of a run.

The list at the bottom is the history of what happened on this project, with the time beside each line.

## Read a result

The desk uses a small set of labels. Read the label that is actually on the run.

- Reproduced within contract. The run finished and the check matched the contract you approved.
- Executed, not verified. The notebook finished. The contract check did not confirm it.
- Changed result. The result is different from the contract.
- Blocked, missing evidence. Something the check needed was not there. The desk abstains.
- Execution failed. The notebook did not finish.
- Not run. Nothing has been run yet.
- Refused, no sandbox. This notebook is outside the three practice cases, so it will not run.
- Finished and Failed describe the execution itself. They are separate from the contract verdict.

## Write a record

1. Open Record in the sidebar.
2. If you have not opened a project yet, the page says there is nothing to claim. Go back to the desk and open a case.
3. Choose the project.
4. Choose Draft from the records. The page quotes the snapshot, the contract, and the runs. It does not invent a paper.
5. When you have read it, choose Mark the draft reviewed. That mark means you reviewed the draft. It does not turn the draft into primary evidence.
6. If evidence is missing, the status stays Abstained.

## Keep a calendar

1. Open Calendar.
2. Type a title, such as Review the repair.
3. Type the local time as a single timestamp, for example `2026-11-01T01:30`.
4. Type the time zone, for example `Europe/London`.
5. If that local hour happens twice in the year, choose the earlier instant or the later instant. If you leave it unspecified, the desk asks you to choose.
6. Choose Add to the internal calendar. The saved line shows the title, the UTC time, and the zone you named.

Choose Download the calendar as ICS if you want a calendar file of those events. You can open that file in another calendar program. Google Calendar is not connected.

## Connectors

Open Connectors. Working means this computer checked that service. Needs configuration means the sign-in is missing.

- GitHub shows the account signed in on this computer. Choose one of your projects, type a repository that account can write, and choose Export. Tick the box only if you want a new private repository under that account. The RETRACE application repository is refused.
- Slack stays unset until you paste a token from your own workspace. After it connects, choose a project and a channel. The message is the project title and question. The notebook is not sent.
- Google Calendar stays unset because this desk has not signed in to Google. Open the desk calendar, download the calendar file, and import that file into your own Google Calendar.
- Colab stays unset. Choose a project and download the notebook, then open Colab and upload it to your account. Notebooks are not sent to Colab, and this desk does not run them there.
- Tools on this computer can read whether the desk is running, which of your accounts are connected, and the name and question of each of your projects. They cannot run a notebook or send the work anywhere.

## Settings

1. Open Settings.
2. Read the notes. They say which notebooks can run, and that the database is local.
3. The personal settings here are the same ones in the name menu: theme, density, language, and clock zone.
4. The model list says Configured, not called when a key is present, and Needs configuration when it is not. Neither state sends a notebook to a provider.

## Bring in a bundle

1. On the desk, find Import an evidence bundle.
2. Choose a `.zip` file a colleague exported.
3. Choose Import bundle. The desk checks the file and opens the project if the check passes.
4. You can read that project. If it is not one of the three practice notebooks, Run will refuse it and the status will say there is no sandbox.

The claimed status inside a bundle is the other person’s claim. It becomes a check on your desk only after you run it here, and only when this desk is allowed to run it.

## If something goes wrong

- The page says the RETRACE service is not running. Start the service from the project folder, then reload this page.
- A time zone is rejected. Use a name such as `Europe/London` or `UTC`.
- A calendar time is ambiguous. Choose the earlier or the later instant and submit again.
- You cannot approve a repair. Approve a contract first.
- Run does nothing for an imported notebook. That refusal is the current limit of this workstation.
- The address is unknown. Use Return to the desk on the recovery page.
- You want the previous person’s view. Sign out, then sign in with that display name. There is no shared password.

RETRACE is maintained by Frank Asante Van Laarhoven.
