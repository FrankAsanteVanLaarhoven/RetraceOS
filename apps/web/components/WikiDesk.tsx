"use client";

import { useState } from "react";
import { useDesk } from "@/components/DeskProvider";
import { Notice } from "@/components/Status";
import type { ApiError, ProjectBrief } from "@/lib/types";

export function WikiDesk({ projects }: { projects: ProjectBrief[] }) {
  const { t } = useDesk();
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

  if (projects.length === 0) {
    return (
      <>
        <p className="eyebrow">{t("wiki.eyebrow")}</p>
        <h1>{t("wiki.title")}</h1>
        <p>{t("wiki.empty")}</p>
      </>
    );
  }

  return (
    <>
      <p className="eyebrow">{t("wiki.eyebrow")}</p>
      <h1>{t("wiki.title")}</h1>
      <p className="lede">{t("wiki.lede")}</p>
      <div className="field">
        <label htmlFor="project">{t("wiki.project")}</label>
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
          {pending === "draft" ? t("wiki.drafting") : t("wiki.draft")}
        </button>
        <button className="ghost" type="button" disabled={!projectId || pending !== null} onClick={() => call(`/api/projects/${projectId}/wiki/review`, "review")}>
          {pending === "review" ? t("wiki.reviewing") : t("wiki.review")}
        </button>
      </div>
      {error?.message ? <Notice message={error.message} next={error.next} /> : null}
      {page ? (
        <article className="panel">
          <p className="k">{page.status === "abstained" ? t("wiki.abstained") : page.status === "reviewed" ? t("wiki.reviewed") : t("wiki.draftStatus")}</p>
          <pre className="keep-ltr">{page.body}</pre>
        </article>
      ) : (
        <p>{t("wiki.hint")}</p>
      )}
    </>
  );
}
