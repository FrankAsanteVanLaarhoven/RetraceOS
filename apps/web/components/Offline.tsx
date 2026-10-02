import { Copy, ViewTitle } from "@/components/Copy";

export function Offline() {
  return (
    <main className="main" id="content">
      <ViewTitle k="offline.title" />
      <Copy as="p" className="eyebrow" k="offline.eyebrow" />
      <Copy as="h1" k="offline.title" />
      <Copy as="p" k="offline.body" />
      <pre className="keep-ltr">.venv/bin/python -m retrace.api</pre>
    </main>
  );
}
