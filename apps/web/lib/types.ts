export type ProjectBrief = {
  id: string;
  name: string;
  discipline: string;
  question: string;
  demo_slug: string | null;
  version: number;
  demo: boolean;
  created_at: string | null;
};

export type Check = {
  name: string;
  unit: string;
  passed: boolean;
  expected: string | null;
  actual: string | null;
  detail: string;
};

export type RunRecord = {
  id: string;
  approval_id: string | null;
  proposal_id: string | null;
  contract_id: string | null;
  execution_status: string;
  verification_status: string;
  explanation: string;
  checks: Check[];
  results: Record<string, unknown> | null;
  log: string;
  started_at: string | null;
  finished_at: string | null;
};

export type Proposal = {
  id: string;
  slug: string;
  title: string;
  classification: string;
  author: string;
  injected: boolean;
  rationale: string;
  find_text: string;
  replace_text: string;
  patch_hash: string;
  status: string;
};

export type Contract = {
  id: string;
  version: number;
  status: string;
  body_hash: string;
  approved_at: string | null;
  body: {
    title: string;
    reference_established: string;
    reference_note: string;
    population: string;
    exclusions: string;
    limitations: string;
    units: Record<string, string>;
    outputs: Array<{
      name: string;
      unit: string;
      comparison: string;
      expected: number | null;
      tolerance: number | null;
      required: boolean;
    }>;
  };
};

export type ProjectView = {
  project: ProjectBrief;
  snapshot: {
    id: string;
    content_hash: string;
    notebook_path: string;
    notebook_json: string;
    allowlisted: boolean;
    execution: string;
    files: Array<{ path: string; sha256: string; size: number }>;
  };
  contracts: Contract[];
  proposals: Proposal[];
  approvals: Array<{
    id: string;
    proposal_id: string;
    contract_id: string;
    candidate_hash: string;
    action_digest: string;
    invalidated_at: string | null;
    invalid_reason: string | null;
  }>;
  runs: RunRecord[];
  events: Array<{ at: string | null; kind: string; summary: string }>;
  lineage: {
    nodes: Array<{ id: string; type: string; label: string; status: string }>;
    edges: Array<{ source: string; target: string; kind: string; observed: boolean }>;
  };
  layout: { version: number; plan: { panels: string[]; inspector: boolean; focus: string | null } } | null;
  wiki: { status: string; body: string; version: number } | null;
};

export type ApiError = { error?: string; message?: string; next?: string };

export function notebookCode(raw: string): string {
  try {
    const notebook = JSON.parse(raw) as { cells?: Array<{ cell_type: string; source: string | string[] }> };
    return (notebook.cells ?? [])
      .filter((cell) => cell.cell_type === "code")
      .map((cell) => (Array.isArray(cell.source) ? cell.source.join("") : cell.source))
      .join("\n\n");
  } catch {
    return "The notebook JSON could not be read.";
  }
}

export const STATUS_LABEL: Record<string, string> = {
  REPRODUCED_WITHIN_CONTRACT: "Reproduced within contract",
  EXECUTED_NOT_VERIFIED: "Executed, not verified",
  CHANGED_RESULT: "Changed result",
  BLOCKED_MISSING_EVIDENCE: "Blocked, missing evidence",
  FAILED_EXECUTION: "Execution failed",
  NOT_RUN: "Not run",
  SUCCEEDED: "Finished",
  FAILED: "Failed",
  BLOCKED_UNSANDBOXED: "Refused, no sandbox",
  CANCELLED: "Cancelled",
  execution_repair: "Execution repair",
  methodological_reanalysis: "Methodological reanalysis",
  approved: "Approved",
  draft: "Draft",
  proposed: "Proposed",
};

export function statusLabel(status: string): string {
  return STATUS_LABEL[status] ?? status.replaceAll("_", " ").toLowerCase();
}

export function statusMark(status: string): string {
  if (status === "REPRODUCED_WITHIN_CONTRACT" || status === "approved") return "✓";
  if (status === "CHANGED_RESULT" || status === "FAILED_EXECUTION" || status === "FAILED") return "Δ";
  if (status === "BLOCKED_MISSING_EVIDENCE" || status === "BLOCKED_UNSANDBOXED" || status === "NOT_RUN") return "–";
  if (status === "EXECUTED_NOT_VERIFIED") return "○";
  return "·";
}
