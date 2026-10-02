export function Offline() {
  return (
    <main className="main" id="content">
      <p className="eyebrow">Workstation</p>
      <h1>The RETRACE service is not running.</h1>
      <p>Start it from the project directory, then reload this page.</p>
      <pre>.venv/bin/python -m retrace.api</pre>
    </main>
  );
}
