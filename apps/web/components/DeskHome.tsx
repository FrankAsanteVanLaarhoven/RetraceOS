"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Notice } from "@/components/Status";
import type { ApiError, ProjectBrief } from "@/lib/types";

const CASES = [
  {
    slug: "ecology",
    index: "01",
    title: "Ecology measurements",
    copy: "A path from another computer, a mean mass in grams, and a trap that drops a record.",
  },
  {
    slug: "trajectory",
    index: "02",
    title: "Trajectory length",
    copy: "A missing filename, a length that must stay in metres, and a trap that leaves centimetres in place.",
  },
  {
    slug: "assay",
    index: "03",
    title: "Assay table",
    copy: "A semicolon-separated table, a mean of every sample, and a trap that adds an exclusion.",
  },
];

export function DeskHome({ projects }: { projects: ProjectBrief[] }) {
  const router = useRouter();
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
      <p className="eyebrow">Workstation profile · demonstrations</p>
      <h1>Recover the analysis without changing what it means.</h1>
      <p className="lede">
        RETRACE keeps the original notebook, asks you to approve a result contract, and will not call a changed analysis reproduced.
        These three cases are labelled fixtures. The faults in them were injected.
      </p>
      {error?.message ? <Notice message={error.message} next={error.next} /> : null}
      <div className="cards">
        {CASES.map((item) => (
          <article className="card" key={item.slug}>
            <div className="index">DEMO {item.index}</div>
            <h2>{item.title}</h2>
            <p>{item.copy}</p>
            <button className="primary" type="button" disabled={pending !== null} onClick={() => openCase(item.slug)}>
              {pending === item.slug ? "Opening the case…" : "Open this case"}
            </button>
          </article>
        ))}
      </div>
      <section className="panel" style={{ marginTop: 24 }}>
        <h2>Already on this desk</h2>
        {projects.length === 0 ? <p>Open a demonstration, or import an evidence bundle from a colleague.</p> : null}
        <ul>
          {projects.map((project) => (
            <li key={project.id}>
              <a href={`/projects/${project.id}`}>{project.name}</a>
              {project.demo ? " · demonstration" : ""}
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
      <label htmlFor="bundle">Import an evidence bundle</label>
      <input id="bundle" name="upload" type="file" accept=".zip,application/zip" required />
      <button className="ghost" type="submit" disabled={pending}>
        {pending ? "Checking the bundle…" : "Import bundle"}
      </button>
      {error?.message ? <Notice message={error.message} next={error.next} /> : null}
    </form>
  );
}
