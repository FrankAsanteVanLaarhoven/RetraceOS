export function GuideDesk() {
  return (
    <article className="guide">
      <p className="eyebrow">Start here</p>
      <h1>How to use this desk</h1>
      <p className="lede">
        RETRACE is a local desk for looking at a computational analysis, keeping the original notebook, and checking a result against a contract you approved. This page walks through every part of the screen in order.
      </p>
      <p>The steps below are in English, the reviewed language of this desk, so they stay exact.</p>

      <ol className="contents">
        <li><a href="#what">What this desk is for</a></li>
        <li><a href="#limits">What it will not claim</a></li>
        <li><a href="#sign-in">Sign in</a></li>
        <li><a href="#screen">Find your way around</a></li>
        <li><a href="#account">Theme, language, clock, and sign out</a></li>
        <li><a href="#case">Open a practice case</a></li>
        <li><a href="#project">Work through a project</a></li>
        <li><a href="#words">Read a result</a></li>
        <li><a href="#record">Write a record</a></li>
        <li><a href="#calendar">Keep a calendar</a></li>
        <li><a href="#connectors">Connectors</a></li>
        <li><a href="#settings">Settings</a></li>
        <li><a href="#import">Bring in a bundle</a></li>
        <li><a href="#trouble">If something goes wrong</a></li>
      </ol>

      <section id="what">
        <h2>What this desk is for</h2>
        <p>Use RETRACE when you want to recover an analysis and still be able to say what changed.</p>
        <ol>
          <li>Keep an untouched copy of the notebook. That copy is the snapshot.</li>
          <li>Write down the result you are willing to accept. That is the contract. Approve it before you treat a run as a check.</li>
          <li>Look at a proposed change. A small repair of the run is a different decision from a change of method.</li>
          <li>Run the original, and later run only the exact change you approved.</li>
          <li>Download a bundle another person can inspect. They still have to run it themselves.</li>
        </ol>
      </section>

      <section id="limits">
        <h2>What it will not claim</h2>
        <ul>
          <li>A number that matches the contract is a numerical check. It does not prove that a scientific conclusion is correct.</li>
          <li>Only three practice notebooks can run. Any other notebook can be opened and read. It will not run, because no tested sandbox is set up.</li>
          <li>GitHub is working when this computer is signed in to a GitHub account. Export sends a project to a repository that account can write. It does not use the RETRACE application repository. Slack shares a project title only after you connect your own workspace. Google Calendar is not signed in; download the calendar file and import it into your own calendar. Colab stays unset, and notebooks are not sent there to run. Download a notebook and open it in your own Colab. Tools on this computer can read your project names and questions. They cannot run a notebook.</li>
          <li>The desk stores its own calendar. It does not talk to Google Calendar.</li>
          <li>Repairs are not sent to a model. Talk calls OpenRouter when the desk server has a key. It does not send notebooks or stored results, and it cannot approve a contract or assign a reproduction result. A missing key leaves Talk unconfigured.</li>
          <li>The database is a local file on this workstation. It is not an institutional database with row-level security.</li>
          <li>A Vercel deployment serves the same desk over HTTPS. Set OPENROUTER_API_KEY for Talk. Set RETRACE_DATABASE_URL to a PostgreSQL URL if accounts must remain after the host restarts. Row-level security is not claimed. A vercel.app address is a preview.</li>
          <li>English is the reviewed language. Other languages change the buttons and headings. They are drafts, and the screen says so. Project names, notebook text, and stored results stay in the language they were written in.</li>
        </ul>
      </section>

      <section id="sign-in">
        <h2>Sign in</h2>
        <ol>
          <li>RETRACE is a public platform for scientists. On this computer the address is <span className="keep-ltr">http://127.0.0.1:3011</span>.</li>
          <li>Type the name that should appear on your record. Choose Continue. Privacy and your record says what is stored.</li>
          <li>There is no password in this build. Each name is a separate scientist account. The session cookie is named retrace_session. It is HttpOnly, lasts 12 hours, and is not an advertising cookie.</li>
          <li>Settings can download your record or delete the account. Deletion removes the projects, the session, and any saved token from this service.</li>
        </ol>
      </section>

      <section id="screen">
        <h2>Find your way around</h2>
        <p>After you sign in, the screen has three areas.</p>
        <h3>Top bar</h3>
        <ul>
          <li>The RETRACE mark on the left returns you to the desk.</li>
          <li>The clock shows the time. If your clock zone is UTC, you see that time once. If you choose another zone, your zone is on the first line and UTC is on the second line.</li>
          <li>The round button switches between a light page and a dark page.</li>
          <li>Your name opens your personal settings. Sign out is inside that menu.</li>
        </ul>
        <h3>Sidebar</h3>
        <ol>
          <li>Desk is the home page, with the three practice cases.</li>
          <li>How to use, in this sidebar, opens and closes this list. Each line opens one section of this page.</li>
          <li>Record drafts a project page from the files already on the desk.</li>
          <li>Calendar stores review times on this workstation.</li>
          <li>Connectors shows outside services. They are not connected.</li>
          <li>Settings describes this workstation.</li>
          <li>Projects lists the cases you have opened. The names stay as they were stored.</li>
        </ol>
        <p>Choose Hide to slide the sidebar away. Move the pointer to the edge control to peek at it. Choose Show to pin it open again. On a phone, Hide becomes a small corner button.</p>
        <h3>Main area</h3>
        <p>The page you chose fills the rest of the screen. The large heading is the title of that page.</p>
      </section>

      <section id="account">
        <h2>Theme, language, clock, and sign out</h2>
        <ol>
          <li>Choose the round button in the top bar. A moon switches to the dark page. A sun switches to the light page. The choice remains after you reload.</li>
          <li>Choose your name. A menu opens.</li>
          <li>Theme can follow the computer, stay light, or stay dark.</li>
          <li>Density can be comfortable or compact. Compact fits more on the screen.</li>
          <li>Language changes the interface. English is the reviewed text. Any other language is a draft, and the menu says that.</li>
          <li>Clock time zone is a name such as <span className="keep-ltr">UTC</span> or <span className="keep-ltr">Europe/London</span>. Leave the field to save it. If the name is not recognised, the menu tells you what to type instead.</li>
          <li>Choose Sign out. You return to the sign-in page. Your projects stay on this computer under the name you used.</li>
          <li>Press Escape, or click outside the menu, to close it without signing out.</li>
        </ol>
        <p>The same four settings are also on the Settings page.</p>
      </section>

      <section id="case">
        <h2>Open a practice case</h2>
        <p>The desk opens with three labelled demonstrations. The faults in them were put there on purpose, so you can see how the desk treats them.</p>
        <ol>
          <li>Ecology measurements. A file path from another computer, a mean mass in grams, and a trap that drops a record.</li>
          <li>Trajectory length. A missing file name, a length that must stay in metres, and a trap that leaves centimetres in place.</li>
          <li>Assay table. A table separated by semicolons, a mean of every sample, and a trap that adds an exclusion.</li>
        </ol>
        <p>Choose Open this case on a card. The project opens. If you have opened it before, it is also listed under Already on this desk and in the sidebar.</p>
      </section>

      <section id="project">
        <h2>Work through a project</h2>
        <p>A project has six stages. Use them in this order. The row of buttons under the title switches stage. You can also use the left and right arrow keys when a stage button is focused.</p>
        <h3>1. Snapshot</h3>
        <p>Read the untouched notebook. The long code under it is the notebook’s fingerprint. If the file changes, that code changes too. On a practice case, the desk says only that demonstration is allowed to run.</p>
        <h3>2. Contract</h3>
        <p>A contract says what result you will accept: who is included, what is excluded, the output, the expected value, and the unit. Choose Approve this contract. After that, a repair cannot edit the contract. If no contract is approved, nothing can be called reproduced.</p>
        <h3>3. Review</h3>
        <p>Read the proposed change. Removed lines and inserted lines are shown separately.</p>
        <ul>
          <li>An execution repair tries to make the same method run.</li>
          <li>A methodological reanalysis changes the method, such as the unit, the exclusions, or who is counted. It stays a reanalysis even if a number still matches.</li>
        </ul>
        <p>Choose the contract this change is judged against, then approve the repair or approve it as a reanalysis. Approving a reanalysis does not produce a reproduced status. You need an approved contract before you can approve the change.</p>
        <h3>4. Run</h3>
        <ol>
          <li>Choose Run the untouched snapshot. That is the original, before any repair.</li>
          <li>After a repair is approved, choose Run on that exact approved candidate.</li>
          <li>Read the execution line, then each check: expected, actual, and whether it passed.</li>
        </ol>
        <p>A package that is not a practice case can be inspected. The Run button will not start it.</p>
        <h3>5. Evidence</h3>
        <p>Finish a run first. Then choose the bundle link. The file contains the snapshot, the change, the contract, and a claimed status. Another account has to run it again. The claimed status is not a verification on their desk. Agreement with the contract is still not proof that the scientific conclusion is correct.</p>
        <h3>6. Lineage</h3>
        <p>The table shows where each relationship came from and where it goes. Observed means a check finished. Proposed means the change has only been suggested.</p>
        <h3>The side panel and the arrangement</h3>
        <p>The panel on the right describes the contract or repair you select. It also repeats the limit: a matching number does not establish the conclusion.</p>
        <p>The arrange field under the title can reorder the panels. It cannot approve a repair or start a run. Open Arrange panels if you want to drag a row, move it with the buttons, undo, or save the arrangement. Saving the arrangement does not hide the status of a run.</p>
        <p>The list at the bottom is the history of what happened on this project, with the time beside each line.</p>
      </section>

      <section id="words">
        <h2>Read a result</h2>
        <p>The desk uses a small set of labels. Read the label that is actually on the run.</p>
        <ul>
          <li>Reproduced within contract. The run finished and the check matched the contract you approved.</li>
          <li>Executed, not verified. The notebook finished. The contract check did not confirm it.</li>
          <li>Changed result. The result is different from the contract.</li>
          <li>Blocked, missing evidence. Something the check needed was not there. The desk abstains.</li>
          <li>Execution failed. The notebook did not finish.</li>
          <li>Not run. Nothing has been run yet.</li>
          <li>Refused, no sandbox. This notebook is outside the three practice cases, so it will not run.</li>
          <li>Finished and Failed describe the execution itself. They are separate from the contract verdict.</li>
        </ul>
      </section>

      <section id="record">
        <h2>Write a record</h2>
        <ol>
          <li>Open Record in the sidebar.</li>
          <li>If you have not opened a project yet, the page says there is nothing to claim. Go back to the desk and open a case.</li>
          <li>Choose the project.</li>
          <li>Choose Draft from the records. The page quotes the snapshot, the contract, and the runs. It does not invent a paper.</li>
          <li>When you have read it, choose Mark the draft reviewed. That mark means you reviewed the draft. It does not turn the draft into primary evidence.</li>
          <li>If evidence is missing, the status stays Abstained.</li>
        </ol>
      </section>

      <section id="calendar">
        <h2>Keep a calendar</h2>
        <ol>
          <li>Open Calendar.</li>
          <li>Type a title, such as Review the repair.</li>
          <li>Type the local time as a single timestamp, for example <span className="keep-ltr">2026-11-01T01:30</span>.</li>
          <li>Type the time zone, for example <span className="keep-ltr">Europe/London</span>.</li>
          <li>If that local hour happens twice in the year, choose the earlier instant or the later instant. If you leave it unspecified, the desk asks you to choose.</li>
          <li>Choose Add to the internal calendar. The saved line shows the title, the UTC time, and the zone you named.</li>
        </ol>
        <p>Choose Download the calendar as ICS if you want a calendar file of those events. You can open that file in another calendar program. Google Calendar is not connected.</p>
      </section>

      <section id="connectors">
        <h2>Connectors</h2>
        <p>Open Connectors. Working means this computer checked that service. Needs configuration means the sign-in is missing.</p>
        <ul>
          <li>GitHub shows the account signed in on this computer. Choose one of your projects, type a repository that account can write, and choose Export. Tick the box only if you want a new private repository under that account. The RETRACE application repository is refused.</li>
          <li>Slack stays unset until you paste a token from your own workspace. After it connects, choose a project and a channel. The message is the project title and question. The notebook is not sent.</li>
          <li>Google Calendar stays unset because this desk has not signed in to Google. Open the desk calendar, download the calendar file, and import that file into your own Google Calendar.</li>
          <li>Colab stays unset. Choose a project and download the notebook, then open Colab and upload it to your account. Notebooks are not sent to Colab, and this desk does not run them there.</li>
          <li>Tools on this computer can read whether the desk is running, which of your accounts are connected, and the name and question of each of your projects. They cannot run a notebook or send the work anywhere.</li>
        </ul>
      </section>

      <section id="settings">
        <h2>Settings</h2>
        <ol>
          <li>Open Settings.</li>
          <li>Read the notes. They say which notebooks can run, and that the database is local.</li>
          <li>The personal settings here are the same ones in the name menu: theme, density, language, and clock zone.</li>
          <li>The model list says Configured, not called when a key is present, and Needs configuration when it is not. Neither state sends a notebook to a provider.</li>
        </ol>
      </section>

      <section id="import">
        <h2>Bring in a bundle</h2>
        <ol>
          <li>On the desk, find Import an evidence bundle.</li>
          <li>Choose a <span className="keep-ltr">.zip</span> file a colleague exported.</li>
          <li>Choose Import bundle. The desk checks the file and opens the project if the check passes.</li>
          <li>You can read that project. If it is not one of the three practice notebooks, Run will refuse it and the status will say there is no sandbox.</li>
        </ol>
        <p>The claimed status inside a bundle is the other person’s claim. It becomes a check on your desk only after you run it here, and only when this desk is allowed to run it.</p>
      </section>

      <section id="trouble">
        <h2>If something goes wrong</h2>
        <ul>
          <li>The page says the RETRACE service is not running. Start the service from the project folder, then reload this page.</li>
          <li>A time zone is rejected. Use a name such as <span className="keep-ltr">Europe/London</span> or <span className="keep-ltr">UTC</span>.</li>
          <li>A calendar time is ambiguous. Choose the earlier or the later instant and submit again.</li>
          <li>You cannot approve a repair. Approve a contract first.</li>
          <li>Run does nothing for an imported notebook. That refusal is the current limit of this workstation.</li>
          <li>The address is unknown. Use Return to the desk on the recovery page.</li>
          <li>You want the previous person’s view. Sign out, then sign in with that display name. There is no shared password.</li>
        </ul>
        <p>RETRACE is maintained by Frank Asante Van Laarhoven. The same steps are written in the project file <span className="keep-ltr">docs/HOW_TO_USE.md</span>.</p>
      </section>
    </article>
  );
}
