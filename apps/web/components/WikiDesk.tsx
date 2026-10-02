"use client";

import { useState } from "react";
import { Notice } from "@/components/Status";
import type { ApiError, ProjectBrief } from "@/lib/types";

export function WikiDesk({ projects }: { projects: ProjectBrief[] }) {
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const [page, setPage] = useState<{ status: string; body: string } | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [pending, setPending] = useState<string | null>(null);

  async function call(path: string, label: string) {
    setPending(label);
    setError(null);
    const response = await fetch(path, { method: "POST" });
    const body = (await response.json()) as ApiError & { status?: string; body?: string };
    setPending(null);
    if (!response.ok || !body.body) {
      setError(body);
      return;
    }
    setPage({ status: body.status ?? "draft", body: body.body });
  }

  if (projects.length === 0) return <p>Open a project before drafting a record. There is nothing to claim yet.</p>;

  return (
    <>
      <div className="field">
        <label htmlFor="project">Project</label>
        <select id="project" value={projectId} onChange={(event) => setProjectId(event.target.value)}>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>
      <div className="actions">
        <button className="primary" type="button" disabled={!projectId || pending !== null} onClick={() => call(`/api/projects/${projectId}/wiki`, "draft")}>
          {pending === "draft" ? "Drafting from the records…" : "Draft from the records"}
        </button>
        <button className="ghost" type="button" disabled={!projectId || pending !== null} onClick={() => call(`/api/projects/${projectId}/wiki/review`, "review")}>
          {pending === "review" ? "Recording the review…" : "Mark the draft reviewed"}
        </button>
      </div>
      {error?.message ? <Notice message={error.message} next={error.next} /> : null}
      {page ? (
        <article className="panel">
          <p className="k">{page.status === "abstained" ? "Abstained" : page.status === "reviewed" ? "Reviewed by the operator" : "Draft, not primary evidence"}</p>
          <pre>{page.body}</pre>
        </article>
      ) : (
        <p>The draft quotes project records. It does not invent a paper.</p>
      )}
    </>
  );
}
