"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useDesk } from "@/components/DeskProvider";
import { Notice } from "@/components/Status";
import type { ApiError, ProjectBrief } from "@/lib/types";

const CASES = [
  { slug: "ecology", index: "01", title: "case.ecology.title", copy: "case.ecology.copy" },
  { slug: "trajectory", index: "02", title: "case.trajectory.title", copy: "case.trajectory.copy" },
  { slug: "assay", index: "03", title: "case.assay.title", copy: "case.assay.copy" },
];

export function DeskHome({ projects }: { projects: ProjectBrief[] }) {
  const router = useRouter();
  const { t } = useDesk();
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState<ApiError | null>(null);

  async function openCase(slug: string) {
    setPending(slug);
    setError(null);
    const response = await fetch(`/api/demos/${slug}`, { method: "POST" });
    const body = (await response.json()) as ApiError & { project?: { id: string } };
    setPending(null);
    if (!response.ok || !body.project) {
      setError(body);
      return;
    }
    router.push(`/projects/${body.project.id}`);
    router.refresh();
  }

  return (
    <>
      <p className="eyebrow">{t("desk.eyebrow")}</p>
      <h1>{t("desk.title")}</h1>
      <p className="lede">{t("desk.lede")}</p>
      <p>
        <a className="text-link" href="/guide">{t("desk.guide")}</a>
      </p>
      {error?.message ? <Notice message={error.message} next={error.next} /> : null}
      <div className="cards">
        {CASES.map((item) => (
          <article className="card" key={item.slug}>
            <div className="index">DEMO {item.index}</div>
            <h2>{t(item.title)}</h2>
            <p>{t(item.copy)}</p>
            <button className="primary" type="button" disabled={pending !== null} onClick={() => openCase(item.slug)}>
              {pending === item.slug ? t("desk.opening") : t("desk.open")}
            </button>
          </article>
        ))}
      </div>
      <section className="panel" style={{ marginTop: 24 }}>
        <h2>{t("desk.already")}</h2>
        {projects.length === 0 ? <p>{t("desk.empty")}</p> : null}
        <ul>
          {projects.map((project) => (
            <li key={project.id}>
              <a href={`/projects/${project.id}`}>{project.name}</a>
              {project.demo ? ` · ${t("desk.demonstration")}` : ""}
            </li>
          ))}
        </ul>
        <ImportBundle />
      </section>
    </>
  );
}

function ImportBundle() {
  const router = useRouter();
  const { t } = useDesk();
  const [error, setError] = useState<ApiError | null>(null);
  const [pending, setPending] = useState(false);

  return (
    <form
      className="field"
      onSubmit={async (event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        setPending(true);
        setError(null);
        const response = await fetch("/api/bundles", { method: "POST", body: data });
        const body = (await response.json()) as ApiError & { project?: { id: string } };
        setPending(false);
        if (!response.ok || !body.project) {
          setError(body);
          return;
        }
        router.push(`/projects/${body.project.id}`);
        router.refresh();
      }}
    >
      <label htmlFor="bundle">{t("desk.importLabel")}</label>
      <input id="bundle" name="upload" type="file" accept=".zip,application/zip" required />
      <button className="ghost" type="submit" disabled={pending}>
        {pending ? t("desk.checking") : t("desk.import")}
      </button>
      {error?.message ? <Notice message={error.message} next={error.next} /> : null}
    </form>
  );
}
