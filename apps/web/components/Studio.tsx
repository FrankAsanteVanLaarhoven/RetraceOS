"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { Notice, Outcome } from "@/components/Status";
import { notebookCode, statusLabel, type ApiError, type ProjectView, type Proposal } from "@/lib/types";

const TABS = [
  ["snapshot", "Snapshot"],
  ["contract", "Contract"],
  ["review", "Review"],
  ["run", "Run"],
  ["evidence", "Evidence"],
  ["lineage", "Lineage"],
] as const;

type Tab = (typeof TABS)[number][0];

export function Studio({ initial }: { initial: ProjectView }) {
  const router = useRouter();
  const [view, setView] = useState(initial);
  const [tab, setTab] = useState<Tab>("snapshot");
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [selected, setSelected] = useState(initial.proposals[0]?.id ?? initial.contracts[0]?.id ?? initial.snapshot.id);
  const [prompt, setPrompt] = useState("");
  const [promptNote, setPromptNote] = useState<string | null>(null);
  const [panels, setPanels] = useState<string[]>(initial.layout?.plan.panels ?? ["brief", "proposal", "checks"]);
  const [past, setPast] = useState<string[][]>([]);
  const [future, setFuture] = useState<string[][]>([]);
  const [drag, setDrag] = useState<string | null>(null);

  const code = useMemo(() => notebookCode(view.snapshot.notebook_json), [view.snapshot.notebook_json]);
  const projectId = view.project.id;

  async function send(label: string, path: string, init?: RequestInit) {
    setPending(label);
    setError(null);
    const response = await fetch(path, init);
    const body = (await response.json().catch(() => ({}))) as ApiError & { project?: ProjectView };
    setPending(null);
    if (!response.ok) {
      setError(body);
      return null;
    }
    if (body.project?.snapshot) setView(body.project);
    else if ("snapshot" in body) setView(body as unknown as ProjectView);
    else {
      const fresh = await fetch(`/api/projects/${projectId}`);
      if (fresh.ok) setView((await fresh.json()) as ProjectView);
    }
    router.refresh();
    return body;
  }

  function remember(next: string[]) {
    setPast((items) => [...items, panels]);
    setFuture([]);
    setPanels(next);
  }

  function move(id: string, direction: -1 | 1) {
    const index = panels.indexOf(id);
    const target = index + direction;
    if (index < 0 || target < 0 || target >= panels.length) return;
    const next = panels.slice();
    const [item] = next.splice(index, 1);
    next.splice(target, 0, item);
    remember(next);
  }

  const selection =
    view.proposals.find((item) => item.id === selected) ||
    view.contracts.find((item) => item.id === selected) ||
    null;

  return (
    <>
      <p className="eyebrow">
        {view.project.demo ? "Demonstration · injected faults" : "Imported package"} · {view.project.discipline || "Unspecified field"}
      </p>
      <h1>{view.project.name}</h1>
      <p className="lede">{view.project.question || "No question has been recorded for this package."}</p>
      {error?.message ? <Notice message={error.message} next={error.next} /> : null}
      <form
        className="prompt"
        onSubmit={async (event) => {
          event.preventDefault();
          const body = await send("prompt", "/api/ui-plan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt }),
          });
          const plan = (body as { plan?: { panels?: string[]; focus?: string | null }; note?: string } | null)?.plan;
          if (!plan) return;
          setPromptNote((body as { note?: string }).note ?? null);
          if (plan.panels) remember(plan.panels);
          if (plan.focus && TABS.some(([id]) => id === plan.focus)) setTab(plan.focus as Tab);
        }}
      >
        <label className="k" htmlFor="prompt">
          Arrange
        </label>
        <input
          id="prompt"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder="Compare the repair and the checks"
        />
        <button className="ghost" type="submit" disabled={pending !== null}>
          {pending === "prompt" ? "Checking…" : "Apply layout"}
        </button>
      </form>
      {promptNote ? <p className="missing">{promptNote} The prompt bar cannot approve or run.</p> : null}

      <div className="tabs" role="tablist" aria-label="Analysis stages">
        {TABS.map(([id, label]) => (
          <button
            key={id}
            id={`tab-${id}`}
            role="tab"
            type="button"
            aria-selected={tab === id}
            aria-controls={`panel-${id}`}
            tabIndex={tab === id ? 0 : -1}
            onClick={() => setTab(id)}
            onKeyDown={(event) => {
              const index = TABS.findIndex(([item]) => item === tab);
              const key = event.key;
              if (key !== "ArrowRight" && key !== "ArrowLeft" && key !== "Home" && key !== "End") return;
              event.preventDefault();
              const next =
                key === "Home" ? 0 : key === "End" ? TABS.length - 1 : key === "ArrowRight" ? (index + 1) % TABS.length : (index - 1 + TABS.length) % TABS.length;
              const nextId = TABS[next][0];
              setTab(nextId);
              document.getElementById(`tab-${nextId}`)?.focus();
            }}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="studio">
        <section className="panel" role="tabpanel" id={`panel-${tab}`} aria-labelledby={`tab-${tab}`}>
          {tab === "snapshot" ? <Snapshot view={view} code={code} /> : null}
          {tab === "contract" ? (
            <Contracts
              view={view}
              pending={pending}
              onSelect={setSelected}
              onApprove={(id) => send(id, `/api/projects/${projectId}/contracts/${id}/approve`, { method: "POST" })}
            />
          ) : null}
          {tab === "review" ? (
            <Review
              view={view}
              pending={pending}
              onSelect={setSelected}
              onApprove={(proposalId, contractId) =>
                send(proposalId, `/api/projects/${projectId}/proposals/${proposalId}/approve`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ contract_id: contractId }),
                })
              }
            />
          ) : null}
          {tab === "run" ? (
            <Runs
              view={view}
              pending={pending}
              onBaseline={() =>
                send("baseline", `/api/projects/${projectId}/runs`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ idempotency_key: `baseline-${Date.now()}` }),
                })
              }
              onRun={(approvalId) =>
                send(approvalId, `/api/projects/${projectId}/runs`, {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({ approval_id: approvalId, idempotency_key: `run-${approvalId}-${Date.now()}` }),
                })
              }
            />
          ) : null}
          {tab === "evidence" ? <Evidence view={view} /> : null}
          {tab === "lineage" ? <Lineage view={view} onSelect={setSelected} /> : null}
        </section>
        <Inspector view={view} selection={selection} />
      </div>

      <details className="panel" style={{ marginTop: 16 }}>
        <summary>Arrange panels</summary>
        <p>Drag a row, or use the buttons. Saving does not approve a repair or hide the status of a run.</p>
        <div className="actions">
          <button className="ghost" type="button" onClick={() => { const previous = past.at(-1); if (!previous) return; setPast((items) => items.slice(0, -1)); setFuture((items) => [panels, ...items]); setPanels(previous); }}>
            Undo
          </button>
          <button className="ghost" type="button" onClick={() => { const next = future[0]; if (!next) return; setFuture((items) => items.slice(1)); setPast((items) => [...items, panels]); setPanels(next); }}>
            Redo
          </button>
          <button
            className="primary"
            type="button"
            disabled={pending !== null}
            onClick={() =>
              send("layout", `/api/projects/${projectId}/layout`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  expected_version: view.layout?.version ?? 0,
                  plan: {
                    version: 1,
                    panels,
                    inspector: true,
                    focus: ["notebook", "proposal", "checks", "lineage", "evidence"].includes(tab) ? tab : null,
                  },
                }),
              })
            }
          >
            {pending === "layout" ? "Saving…" : "Save arrangement"}
          </button>
        </div>
        <ol>
          {panels.map((panel) => (
            <li
              key={panel}
              draggable
              onDragStart={() => setDrag(panel)}
              onDragOver={(event) => event.preventDefault()}
              onDrop={() => {
                if (!drag || drag === panel) return;
                const next = panels.filter((item) => item !== drag);
                next.splice(next.indexOf(panel), 0, drag);
                remember(next);
                setDrag(null);
              }}
            >
              {panel}
              <button className="text-button" type="button" onClick={() => move(panel, -1)}>
                Move {panel} up
              </button>
              <button className="text-button" type="button" onClick={() => move(panel, 1)}>
                Move {panel} down
              </button>
            </li>
          ))}
        </ol>
      </details>

      <div className="timeline">
        {view.events.map((event, index) => (
          <article key={`${event.at}-${index}`}>
            <time dateTime={event.at ?? undefined}>{event.at ?? "Undated"}</time>
            <p>{event.summary}</p>
          </article>
        ))}
      </div>
    </>
  );
}

function Snapshot({ view, code }: { view: ProjectView; code: string }) {
  return (
    <>
      <h2>Untouched snapshot</h2>
      <p>
        Execution on this workstation is {view.snapshot.allowlisted ? "limited to this admitted demonstration" : "turned off. No tested sandbox is configured"}.
      </p>
      <p className="hash">{view.snapshot.content_hash}</p>
      <table>
        <thead>
          <tr>
            <th>File</th>
            <th>SHA-256</th>
            <th>Bytes</th>
          </tr>
        </thead>
        <tbody>
          {view.snapshot.files.map((file) => (
            <tr key={file.path}>
              <td>{file.path}</td>
              <td className="hash">{file.sha256}</td>
              <td>{file.size}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>Notebook</h3>
      <pre>{code}</pre>
    </>
  );
}

function Contracts({
  view,
  pending,
  onApprove,
  onSelect,
}: {
  view: ProjectView;
  pending: string | null;
  onApprove: (id: string) => void;
  onSelect: (id: string) => void;
}) {
  if (view.contracts.length === 0) return <p>No result contract has been recorded. Nothing can be called reproduced.</p>;
  return (
    <>
      <h2>Result contracts</h2>
      {view.contracts.map((contract) => (
        <article key={contract.id} onClick={() => onSelect(contract.id)}>
          <h3>{contract.body.title}</h3>
          <Outcome status={contract.status} />
          <p>{contract.body.reference_note}</p>
          <p>
            <span className="k">Population</span> {contract.body.population}
          </p>
          <p>
            <span className="k">Exclusions</span> {contract.body.exclusions}
          </p>
          <table>
            <thead>
              <tr>
                <th>Output</th>
                <th>Expected</th>
                <th>Unit</th>
              </tr>
            </thead>
            <tbody>
              {contract.body.outputs.map((output) => (
                <tr key={output.name}>
                  <td>{output.name}</td>
                  <td>{output.expected === null ? "Not supplied" : String(output.expected)}</td>
                  <td>{output.unit}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p>{contract.body.limitations}</p>
          {contract.status === "draft" ? (
            <button className="primary" type="button" disabled={pending !== null} onClick={() => onApprove(contract.id)}>
              {pending === contract.id ? "Approving…" : "Approve this contract"}
            </button>
          ) : (
            <p>Approved {contract.approved_at}. The repair cannot edit it.</p>
          )}
        </article>
      ))}
    </>
  );
}

function Review({
  view,
  pending,
  onApprove,
  onSelect,
}: {
  view: ProjectView;
  pending: string | null;
  onApprove: (proposalId: string, contractId: string) => void;
  onSelect: (id: string) => void;
}) {
  const approvedContracts = view.contracts.filter((contract) => contract.status === "approved");
  return (
    <>
      <h2>Proposed changes</h2>
      <p>A mechanical repair and a change of method are not the same decision. Method changes stay labelled as reanalysis.</p>
      {view.proposals.map((proposal) => (
        <ProposalCard
          key={proposal.id}
          proposal={proposal}
          pending={pending}
          contracts={approvedContracts.map((contract) => ({ id: contract.id, title: contract.body.title }))}
          onSelect={() => onSelect(proposal.id)}
          onApprove={onApprove}
        />
      ))}
    </>
  );
}

function ProposalCard({
  proposal,
  contracts,
  pending,
  onApprove,
  onSelect,
}: {
  proposal: Proposal;
  contracts: Array<{ id: string; title: string }>;
  pending: string | null;
  onApprove: (proposalId: string, contractId: string) => void;
  onSelect: () => void;
}) {
  const [contractId, setContractId] = useState(contracts[0]?.id ?? "");
  const reanalysis = proposal.classification === "methodological_reanalysis";
  return (
    <article onClick={onSelect}>
      <h3>{proposal.title}</h3>
      <Outcome status={proposal.classification} />
      <p>{proposal.rationale}</p>
      <p>
        Author {proposal.author}
        {proposal.injected ? " · injected demonstration trap" : " · diagnosed from the notebook"}
      </p>
      <div className="split">
        <div>
          <p className="k">Remove</p>
          <pre>{proposal.find_text}</pre>
        </div>
        <div>
          <p className="k">Insert</p>
          <pre>{proposal.replace_text}</pre>
        </div>
      </div>
      {reanalysis ? <p>Approving this will not produce a reproduced status.</p> : null}
      {contracts.length === 0 ? (
        <p>Approve a contract before approving this repair.</p>
      ) : (
        <div className="actions">
          <label>
            Against
            <select value={contractId} onChange={(event) => setContractId(event.target.value)} aria-label={`Contract for ${proposal.title}`}>
              {contracts.map((contract) => (
                <option key={contract.id} value={contract.id}>
                  {contract.title}
                </option>
              ))}
            </select>
          </label>
          <button className="primary" type="button" disabled={pending !== null || !contractId} onClick={() => onApprove(proposal.id, contractId)}>
            {pending === proposal.id ? "Approving…" : reanalysis ? "Approve as reanalysis" : "Approve this repair"}
          </button>
        </div>
      )}
    </article>
  );
}

function Runs({
  view,
  pending,
  onBaseline,
  onRun,
}: {
  view: ProjectView;
  pending: string | null;
  onBaseline: () => void;
  onRun: (approvalId: string) => void;
}) {
  const live = view.approvals.filter((approval) => !approval.invalidated_at);
  return (
    <>
      <h2>Run and compare</h2>
      <div className="actions">
        <button className="ghost" type="button" disabled={pending !== null || !view.snapshot.allowlisted} onClick={onBaseline}>
          {pending === "baseline" ? "Running the original…" : "Run the untouched snapshot"}
        </button>
      </div>
      {!view.snapshot.allowlisted ? <p>This package can be inspected. It will not run until a tested sandbox exists.</p> : null}
      {live.length === 0 ? <p>No current approval. Approve a repair, then run that exact candidate.</p> : null}
      <div className="actions">
        {live.map((approval) => {
          const proposal = view.proposals.find((item) => item.id === approval.proposal_id);
          return (
            <button key={approval.id} className="primary" type="button" disabled={pending !== null} onClick={() => onRun(approval.id)}>
              {pending === approval.id ? "Running…" : `Run “${proposal?.title ?? "approved repair"}”`}
            </button>
          );
        })}
      </div>
      {view.runs.length === 0 ? <p>No runs yet.</p> : null}
      {view.runs.map((run) => (
        <article key={run.id}>
          <Outcome status={run.verification_status} heading />
          <p>Execution: {statusLabel(run.execution_status)}</p>
          <p>{run.explanation}</p>
          {run.checks.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>Check</th>
                  <th>Expected</th>
                  <th>Actual</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {run.checks.map((check) => (
                  <tr key={check.name}>
                    <td>{check.name}</td>
                    <td>{check.expected ?? "Not supplied"}</td>
                    <td>{check.actual ?? "Not produced"}</td>
                    <td>{check.passed ? "Passed" : "Failed"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
          {run.log ? (
            <details>
              <summary>Execution log</summary>
              <pre>{run.log}</pre>
            </details>
          ) : null}
        </article>
      ))}
    </>
  );
}

function Evidence({ view }: { view: ProjectView }) {
  return (
    <>
      <h2>Portable evidence</h2>
      <p>
        A downloaded bundle carries the snapshot, the patch, the contract, and a claimed status. Another account must rerun it. The claimed status is not a verification there.
      </p>
      <p>Agreement with the contract is not proof that a scientific conclusion is correct. A notebook can still emit internally consistent numbers.</p>
      {view.runs.length === 0 ? <p>Finish a run before exporting evidence.</p> : null}
      <ul>
        {view.runs.map((run) => (
          <li key={run.id}>
            <a href={`/api/projects/${view.project.id}/runs/${run.id}/bundle`}>{statusLabel(run.verification_status)} bundle</a>
          </li>
        ))}
      </ul>
    </>
  );
}

function Lineage({ view, onSelect }: { view: ProjectView; onSelect: (id: string) => void }) {
  const labels = new Map(view.lineage.nodes.map((node) => [node.id, node.label]));
  return (
    <>
      <h2>Lineage</h2>
      <p>Observed relationships come from an admitted snapshot or a finished check. A repair that is only proposed is marked as such.</p>
      <table>
        <thead>
          <tr>
            <th>From</th>
            <th>Relation</th>
            <th>To</th>
            <th>Standing</th>
          </tr>
        </thead>
        <tbody>
          {view.lineage.edges.map((edge, index) => (
            <tr key={`${edge.kind}-${index}`}>
              <td>
                <button className="text-button" type="button" onClick={() => onSelect(edge.source)}>
                  {labels.get(edge.source) ?? edge.source.slice(0, 8)}
                </button>
              </td>
              <td>{edge.kind}</td>
              <td>
                <button className="text-button" type="button" onClick={() => onSelect(edge.target)}>
                  {labels.get(edge.target) ?? edge.target.slice(0, 8)}
                </button>
              </td>
              <td>{edge.observed ? "Observed" : "Proposed"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

function Inspector({
  view,
  selection,
}: {
  view: ProjectView;
  selection: Proposal | ProjectView["contracts"][number] | null;
}) {
  return (
    <aside className="inspector" aria-label="Inspector">
      <p className="k">Identity</p>
      <p>{view.project.name}</p>
      <p className="hash">{view.snapshot.content_hash}</p>
      <p className="k">Selected</p>
      {selection && "title" in selection && !("body" in selection) ? (
        <>
          <p>{selection.title}</p>
          <p>{statusLabel(selection.classification)}</p>
          <p className="hash">{selection.patch_hash}</p>
        </>
      ) : null}
      {selection && "body" in selection ? (
        <>
          <p>{selection.body.title}</p>
          <p>{statusLabel(selection.status)}</p>
          <p className="hash">{selection.body_hash}</p>
        </>
      ) : null}
      {!selection ? <p>Select a contract or a repair.</p> : null}
      <p className="k">What this does not show</p>
      <p>A matching number does not establish that the scientific conclusion is correct.</p>
    </aside>
  );
}
