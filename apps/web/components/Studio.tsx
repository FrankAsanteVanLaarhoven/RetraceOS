"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { useDesk } from "@/components/DeskProvider";
import { Notice, Outcome } from "@/components/Status";
import { notebookCode, statusLabel, type ApiError, type ProjectView, type Proposal } from "@/lib/types";

const NOTES: Record<string, string> = {
  "Lineage and the case brief.": "studio.note.lineage",
  "The repair beside its checks.": "studio.note.repair",
  "The evidence bundle and the checks it carries.": "studio.note.evidence",
  "The notebook and the proposed change.": "studio.note.notebook",
};

const TABS = [
  ["snapshot", "tab.snapshot"],
  ["contract", "tab.contract"],
  ["review", "tab.review"],
  ["run", "tab.run"],
  ["evidence", "tab.evidence"],
  ["lineage", "tab.lineage"],
] as const;

type Tab = (typeof TABS)[number][0];

export function Studio({ initial }: { initial: ProjectView }) {
  const router = useRouter();
  const { t } = useDesk();
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
        {view.project.demo ? t("studio.demo") : t("studio.imported")} · {view.project.discipline || t("studio.unspecified")}
      </p>
      <h1>{view.project.name}</h1>
      <p className="lede">{view.project.question || t("studio.noQuestion")}</p>
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
          {t("studio.arrange")}
        </label>
        <input
          id="prompt"
          value={prompt}
          onChange={(event) => setPrompt(event.target.value)}
          placeholder={t("studio.placeholder")}
        />
        <button className="ghost" type="submit" disabled={pending !== null}>
          {pending === "prompt" ? t("studio.checking") : t("studio.apply")}
        </button>
      </form>
      {promptNote ? (
        <p className="missing">
          {NOTES[promptNote] ? t(NOTES[promptNote]) : promptNote} {t("studio.promptNote")}
        </p>
      ) : null}

      <div className="tabs" role="tablist" aria-label={t("studio.tabs")}>
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
            {t(label)}
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
        <summary>{t("studio.arrangePanels")}</summary>
        <p>{t("studio.arrangeHelp")}</p>
        <div className="actions">
          <button className="ghost" type="button" onClick={() => { const previous = past.at(-1); if (!previous) return; setPast((items) => items.slice(0, -1)); setFuture((items) => [panels, ...items]); setPanels(previous); }}>
            {t("studio.undo")}
          </button>
          <button className="ghost" type="button" onClick={() => { const next = future[0]; if (!next) return; setFuture((items) => items.slice(1)); setPast((items) => [...items, panels]); setPanels(next); }}>
            {t("studio.redo")}
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
            {pending === "layout" ? t("studio.saving") : t("studio.save")}
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
              {t(`panel.${panel}`)}
              <button className="text-button" type="button" onClick={() => move(panel, -1)}>
                {t("studio.moveUp", { name: t(`panel.${panel}`) })}
              </button>
              <button className="text-button" type="button" onClick={() => move(panel, 1)}>
                {t("studio.moveDown", { name: t(`panel.${panel}`) })}
              </button>
            </li>
          ))}
        </ol>
      </details>

      <div className="timeline">
        {view.events.map((event, index) => (
          <article key={`${event.at}-${index}`}>
            <time dateTime={event.at ?? undefined}>{event.at ?? t("studio.undated")}</time>
            <p>{event.summary}</p>
          </article>
        ))}
      </div>
    </>
  );
}

function Snapshot({ view, code }: { view: ProjectView; code: string }) {
  const { t } = useDesk();
  return (
    <>
      <h2>{t("snap.title")}</h2>
      <p>{view.snapshot.allowlisted ? t("snap.limited") : t("snap.off")}</p>
      <p className="hash">{view.snapshot.content_hash}</p>
      <table>
        <thead>
          <tr>
            <th>{t("snap.file")}</th>
            <th>{t("snap.hash")}</th>
            <th>{t("snap.bytes")}</th>
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
      <h3>{t("snap.notebook")}</h3>
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
  const { t } = useDesk();
  if (view.contracts.length === 0) return <p>{t("contract.none")}</p>;
  return (
    <>
      <h2>{t("contract.title")}</h2>
      {view.contracts.map((contract) => (
        <article key={contract.id} onClick={() => onSelect(contract.id)}>
          <h3>{contract.body.title}</h3>
          <Outcome status={contract.status} />
          <p>{contract.body.reference_note}</p>
          <p>
            <span className="k">{t("contract.population")}</span> {contract.body.population}
          </p>
          <p>
            <span className="k">{t("contract.exclusions")}</span> {contract.body.exclusions}
          </p>
          <table>
            <thead>
              <tr>
                <th>{t("contract.output")}</th>
                <th>{t("contract.expected")}</th>
                <th>{t("contract.unit")}</th>
              </tr>
            </thead>
            <tbody>
              {contract.body.outputs.map((output) => (
                <tr key={output.name}>
                  <td>{output.name}</td>
                  <td>{output.expected === null ? t("contract.notSupplied") : String(output.expected)}</td>
                  <td>{output.unit}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p>{contract.body.limitations}</p>
          {contract.status === "draft" ? (
            <button className="primary" type="button" disabled={pending !== null} onClick={() => onApprove(contract.id)}>
              {pending === contract.id ? t("contract.approving") : t("contract.approve")}
            </button>
          ) : (
            <p>{t("contract.approvedAt", { when: contract.approved_at ?? "" })}</p>
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
  const { t } = useDesk();
  const approvedContracts = view.contracts.filter((contract) => contract.status === "approved");
  return (
    <>
      <h2>{t("review.title")}</h2>
      <p>{t("review.lede")}</p>
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
  const { t } = useDesk();
  const [contractId, setContractId] = useState(contracts[0]?.id ?? "");
  const reanalysis = proposal.classification === "methodological_reanalysis";
  return (
    <article onClick={onSelect}>
      <h3>{proposal.title}</h3>
      <Outcome status={proposal.classification} />
      <p>{proposal.rationale}</p>
      <p>
        {t("review.author", { name: proposal.author })}
        {" · "}
        {proposal.injected ? t("review.injected") : t("review.diagnosed")}
      </p>
      <div className="split">
        <div>
          <p className="k">{t("review.remove")}</p>
          <pre className="keep-ltr">{proposal.find_text}</pre>
        </div>
        <div>
          <p className="k">{t("review.insert")}</p>
          <pre className="keep-ltr">{proposal.replace_text}</pre>
        </div>
      </div>
      {reanalysis ? <p>{t("review.noRepro")}</p> : null}
      {contracts.length === 0 ? (
        <p>{t("review.needContract")}</p>
      ) : (
        <div className="actions">
          <label>
            {t("review.against")}
            <select value={contractId} onChange={(event) => setContractId(event.target.value)} aria-label={t("review.contractFor", { title: proposal.title })}>
              {contracts.map((contract) => (
                <option key={contract.id} value={contract.id}>
                  {contract.title}
                </option>
              ))}
            </select>
          </label>
          <button className="primary" type="button" disabled={pending !== null || !contractId} onClick={() => onApprove(proposal.id, contractId)}>
            {pending === proposal.id ? t("review.approving") : reanalysis ? t("review.approveReanalysis") : t("review.approveRepair")}
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
  const { t } = useDesk();
  const live = view.approvals.filter((approval) => !approval.invalidated_at);
  return (
    <>
      <h2>{t("run.title")}</h2>
      <div className="actions">
        <button className="ghost" type="button" disabled={pending !== null || !view.snapshot.allowlisted} onClick={onBaseline}>
          {pending === "baseline" ? t("run.runningOriginal") : t("run.original")}
        </button>
      </div>
      {!view.snapshot.allowlisted ? <p>{t("run.noSandbox")}</p> : null}
      {live.length === 0 ? <p>{t("run.noApproval")}</p> : null}
      <div className="actions">
        {live.map((approval) => {
          const proposal = view.proposals.find((item) => item.id === approval.proposal_id);
          return (
            <button key={approval.id} className="primary" type="button" disabled={pending !== null} onClick={() => onRun(approval.id)}>
              {pending === approval.id ? t("run.running") : t("run.button", { title: proposal?.title ?? t("run.approvedRepair") })}
            </button>
          );
        })}
      </div>
      {view.runs.length === 0 ? <p>{t("run.none")}</p> : null}
      {view.runs.map((run) => (
        <article key={run.id}>
          <Outcome status={run.verification_status} heading />
          <p>{t("run.execution", { status: textStatus(run.execution_status, t) })}</p>
          <p>{run.explanation}</p>
          {run.checks.length > 0 ? (
            <table>
              <thead>
                <tr>
                  <th>{t("run.check")}</th>
                  <th>{t("run.expected")}</th>
                  <th>{t("run.actual")}</th>
                  <th>{t("run.result")}</th>
                </tr>
              </thead>
              <tbody>
                {run.checks.map((check) => (
                  <tr key={check.name}>
                    <td>{check.name}</td>
                    <td>{check.expected ?? t("contract.notSupplied")}</td>
                    <td>{check.actual ?? t("run.notProduced")}</td>
                    <td>{check.passed ? t("run.passed") : t("run.failed")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : null}
          {run.log ? (
            <details>
              <summary>{t("run.log")}</summary>
              <pre>{run.log}</pre>
            </details>
          ) : null}
        </article>
      ))}
    </>
  );
}

function Evidence({ view }: { view: ProjectView }) {
  const { t } = useDesk();
  return (
    <>
      <h2>{t("evidence.title")}</h2>
      <p>{t("evidence.body")}</p>
      <p>{t("evidence.caveat")}</p>
      {view.runs.length === 0 ? <p>{t("evidence.needRun")}</p> : null}
      <ul>
        {view.runs.map((run) => (
          <li key={run.id}>
            <a href={`/api/projects/${view.project.id}/runs/${run.id}/bundle`}>{t("evidence.bundle", { status: textStatus(run.verification_status, t) })}</a>
          </li>
        ))}
      </ul>
    </>
  );
}

function Lineage({ view, onSelect }: { view: ProjectView; onSelect: (id: string) => void }) {
  const { t } = useDesk();
  const labels = new Map(view.lineage.nodes.map((node) => [node.id, node.label]));
  return (
    <>
      <h2>{t("lineage.title")}</h2>
      <p>{t("lineage.lede")}</p>
      <table>
        <thead>
          <tr>
            <th>{t("lineage.from")}</th>
            <th>{t("lineage.relation")}</th>
            <th>{t("lineage.to")}</th>
            <th>{t("lineage.standing")}</th>
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
              <td>{edge.observed ? t("lineage.observed") : t("lineage.proposed")}</td>
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
  const { t } = useDesk();
  return (
    <aside className="inspector" aria-label={t("inspector.label")}>
      <p className="k">{t("inspector.identity")}</p>
      <p>{view.project.name}</p>
      <p className="hash">{view.snapshot.content_hash}</p>
      <p className="k">{t("inspector.selected")}</p>
      {selection && "title" in selection && !("body" in selection) ? (
        <>
          <p>{selection.title}</p>
          <p>{textStatus(selection.classification, t)}</p>
          <p className="hash">{selection.patch_hash}</p>
        </>
      ) : null}
      {selection && "body" in selection ? (
        <>
          <p>{selection.body.title}</p>
          <p>{textStatus(selection.status, t)}</p>
          <p className="hash">{selection.body_hash}</p>
        </>
      ) : null}
      {!selection ? <p>{t("inspector.empty")}</p> : null}
      <p className="k">{t("inspector.limit")}</p>
      <p>{t("inspector.limitBody")}</p>
    </aside>
  );
}

function textStatus(status: string, t: (key: string, vars?: Record<string, string>) => string) {
  const key = `status.${status}`;
  const value = t(key);
  return value === key ? statusLabel(status) : value;
}
