"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Notice } from "@/components/Status";
import { useDesk } from "@/components/DeskProvider";

type Action = { href: string; label: string };
type Connector = { id: string; status: string; detail: string; actions?: Action[]; account?: string | null; notes?: string[] };
type ProjectChoice = { id: string; name: string };
type ApiError = { message?: string; next?: string };
type ExportResult = { url?: string; notebook_url?: string; colab_url?: string; message?: string; next?: string };

const LOGIN = /^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$/;
const REPO = /^[A-Za-z0-9._-]{1,100}$/;
const BRANCH = /^[A-Za-z0-9._-]{1,120}$/;
const PROJECT = /^[a-f0-9]{32}$/;
const FILE = /^[A-Za-z0-9._-]{1,80}$/;

function safeHref(href: string) {
  if (href.startsWith("/") && !href.startsWith("//")) return href;
  if (href === "https://colab.research.google.com/") return href;
  if (href === "https://calendar.google.com/calendar/r") return href;
  let url: URL;
  try {
    url = new URL(href);
  } catch {
    return null;
  }
  if (url.origin === "https://github.com") {
    const parts = url.pathname.split("/").filter(Boolean);
    if (parts.length >= 2 && parts[0].toLowerCase() === "frankasantevanlaarhoven" && parts[1].toLowerCase() === "retraceos") return null;
    if (parts.length === 1 && LOGIN.test(parts[0])) return href;
    if (parts.length === 2 && LOGIN.test(parts[0]) && REPO.test(parts[1])) return href;
    if (
      parts.length === 7 &&
      parts[2] === "blob" &&
      LOGIN.test(parts[0]) &&
      REPO.test(parts[1]) &&
      BRANCH.test(parts[3]) &&
      parts[4] === "retrace" &&
      PROJECT.test(parts[5]) &&
      FILE.test(parts[6])
    ) {
      return href;
    }
  }
  if (url.origin === "https://colab.research.google.com" && url.pathname.startsWith("/github/")) {
    const parts = url.pathname.slice("/github/".length).split("/");
    if (parts.length >= 2 && parts[0].toLowerCase() === "frankasantevanlaarhoven" && parts[1].toLowerCase() === "retraceos") return null;
    if (
      parts.length === 7 &&
      parts[2] === "blob" &&
      LOGIN.test(parts[0]) &&
      REPO.test(parts[1]) &&
      BRANCH.test(parts[3]) &&
      parts[4] === "retrace" &&
      PROJECT.test(parts[5]) &&
      FILE.test(parts[6])
    ) {
      return href;
    }
  }
  return null;
}

function ProjectField({ id, projects, label }: { id: string; projects: ProjectChoice[]; label: string }) {
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select id={id} name="project_id" required disabled={projects.length === 0} defaultValue={projects[0]?.id ?? ""}>
        {projects.length === 0 ? <option value="">{label}</option> : null}
        {projects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name}
          </option>
        ))}
      </select>
    </div>
  );
}

export function ConnectorsDesk({ connectors, projects }: { connectors: Connector[]; projects: ProjectChoice[] }) {
  const { t } = useDesk();
  const router = useRouter();
  return (
    <>
      <p className="eyebrow">{t("connectors.eyebrow")}</p>
      <h1>{t("connectors.title")}</h1>
      <p className="lede">{t("connectors.lede")}</p>
      <div className="cards">
        {connectors.map((connector) => {
          const nameKey = `connectors.name.${connector.id}`;
          const name = t(nameKey);
          const working = connector.status === "OPERATIONAL";
          const links = (connector.actions ?? []).flatMap((action) => {
            const href = safeHref(action.href);
            return href ? [{ href, label: action.label }] : [];
          });
          return (
            <article className="card" key={connector.id} data-status={connector.status}>
              <div className="index" data-state={working ? "working" : "needs"}>
                {working ? t("connectors.working") : t("connectors.needs")}
              </div>
              <h2>{name === nameKey ? connector.id : name}</h2>
              <p>{connector.detail}</p>
              {links.length > 0 ? (
                <p className="card-links">
                  {links.map((action) => (
                    <a
                      key={action.href}
                      className="text-link"
                      href={action.href}
                      {...(action.href.startsWith("http") ? { target: "_blank", rel: "noreferrer" } : {})}
                    >
                      {action.label}
                    </a>
                  ))}
                </p>
              ) : null}
              {connector.id === "github" ? (
                <GitHubShare
                  account={connector.account ?? ""}
                  working={working}
                  projects={projects}
                  onCheck={() => router.refresh()}
                />
              ) : null}
              {connector.id === "slack" ? (
                <SlackShare working={working} projects={projects} onChanged={() => router.refresh()} />
              ) : null}
              {connector.id === "colab" ? <ColabShare projects={projects} /> : null}
              {connector.notes && connector.notes.length > 0 ? (
                <ul className="card-notes">
                  {connector.notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              ) : null}
            </article>
          );
        })}
      </div>
    </>
  );
}

function GitHubShare({
  account,
  working,
  projects,
  onCheck,
}: {
  account: string;
  working: boolean;
  projects: ProjectChoice[];
  onCheck: () => void;
}) {
  const { t } = useDesk();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [result, setResult] = useState<ExportResult | null>(null);
  const links = [result?.url, result?.notebook_url, result?.colab_url].flatMap((href) => {
    const safe = href ? safeHref(href) : null;
    return safe ? [safe] : [];
  });
  if (!working) {
    return (
      <p className="card-links">
        <button className="ghost" type="button" onClick={onCheck}>
          {t("connectors.check")}
        </button>
      </p>
    );
  }
  return (
    <form
      className="card-share"
      onSubmit={async (event) => {
        event.preventDefault();
        const data = new FormData(event.currentTarget);
        setPending(true);
        setError(null);
        setResult(null);
        const response = await fetch("/api/connectors/github/export", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            project_id: data.get("project_id"),
            repository: data.get("repository"),
            create: data.get("create") === "on",
          }),
        });
        const body = (await response.json()) as ApiError & ExportResult;
        setPending(false);
        if (!response.ok) {
          setError(body);
          return;
        }
        setResult(body);
      }}
    >
      <ProjectField id="github-project" projects={projects} label={t("connectors.project")} />
      {projects.length === 0 ? <p>{t("connectors.noProjects")}</p> : null}
      <div className="field">
        <label htmlFor="github-repository">{t("connectors.repository")}</label>
        <input
          id="github-repository"
          name="repository"
          required
          className="keep-ltr"
          autoComplete="off"
          placeholder={account ? `${account}/your-notes` : "your-name/your-notes"}
          spellCheck={false}
        />
      </div>
      <label className="check">
        <input name="create" type="checkbox" />
        <span>{t("connectors.create")}</span>
      </label>
      {error?.message ? <Notice message={error.message} next={error.next} /> : null}
      {result?.message ? (
        <div className="card-result" role="status">
          <strong>{result.message}</strong>
          {result.next ? <span>{result.next}</span> : null}
        </div>
      ) : null}
      {links.length > 0 ? (
        <p className="card-links">
          {links.map((href) => (
            <a key={href} className="text-link" href={href} target="_blank" rel="noreferrer">
              {href.includes("colab.research.google.com")
                ? t("connectors.openColab")
                : href.includes("/blob/")
                  ? t("connectors.openNotebook")
                  : t("connectors.openGithub")}
            </a>
          ))}
        </p>
      ) : null}
      <button className="primary" type="submit" disabled={pending || projects.length === 0} aria-busy={pending}>
        {pending ? t("connectors.exporting") : t("connectors.export")}
      </button>
    </form>
  );
}

function SlackShare({ working, projects, onChanged }: { working: boolean; projects: ProjectChoice[]; onChanged: () => void }) {
  const { t } = useDesk();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);
  const [notice, setNotice] = useState<ApiError | null>(null);
  return (
    <div className="card-share">
      {working ? (
        <form
          onSubmit={async (event) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget);
            setPending(true);
            setError(null);
            setNotice(null);
            const response = await fetch("/api/connectors/slack/share", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ project_id: data.get("project_id"), channel: data.get("channel") }),
            });
            const body = (await response.json()) as ApiError;
            setPending(false);
            if (!response.ok) {
              setError(body);
              return;
            }
            setNotice(body);
          }}
        >
          <ProjectField id="slack-project" projects={projects} label={t("connectors.project")} />
          {projects.length === 0 ? <p>{t("connectors.noProjects")}</p> : null}
          <div className="field">
            <label htmlFor="slack-channel">{t("connectors.channel")}</label>
            <input id="slack-channel" name="channel" required className="keep-ltr" autoComplete="off" placeholder="project-updates" spellCheck={false} />
          </div>
          <button className="primary" type="submit" disabled={pending || projects.length === 0} aria-busy={pending}>
            {pending ? t("connectors.sharing") : t("connectors.share")}
          </button>
        </form>
      ) : (
        <form
          onSubmit={async (event) => {
            event.preventDefault();
            const data = new FormData(event.currentTarget);
            setPending(true);
            setError(null);
            const response = await fetch("/api/connectors/slack", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ token: data.get("token") }),
            });
            const body = (await response.json()) as ApiError;
            setPending(false);
            if (!response.ok) {
              setError(body);
              return;
            }
            onChanged();
          }}
        >
          <div className="field">
            <label htmlFor="slack-token">{t("connectors.token")}</label>
            <input id="slack-token" name="token" type="password" required className="keep-ltr" autoComplete="off" spellCheck={false} />
          </div>
          <button className="primary" type="submit" disabled={pending} aria-busy={pending}>
            {pending ? t("connectors.connecting") : t("connectors.connect")}
          </button>
        </form>
      )}
      {error?.message ? <Notice message={error.message} next={error.next} /> : null}
      {notice?.message ? (
        <div className="card-result" role="status">
          <strong>{notice.message}</strong>
          {notice.next ? <span>{notice.next}</span> : null}
        </div>
      ) : null}
      {working ? (
        <button
          className="ghost"
          type="button"
          onClick={async () => {
            setPending(true);
            setError(null);
            const response = await fetch("/api/connectors/slack/disconnect", { method: "POST" });
            setPending(false);
            if (!response.ok) {
              const body = (await response.json()) as ApiError;
              setError(body);
              return;
            }
            onChanged();
          }}
        >
          {t("connectors.different")}
        </button>
      ) : null}
    </div>
  );
}

function ColabShare({ projects }: { projects: ProjectChoice[] }) {
  const { t } = useDesk();
  const [projectId, setProjectId] = useState(projects[0]?.id ?? "");
  const href = PROJECT.test(projectId) ? `/api/projects/${projectId}/notebook` : "";
  return (
    <div className="card-share">
      <div className="field">
        <label htmlFor="colab-project">{t("connectors.project")}</label>
        <select
          id="colab-project"
          value={projectId}
          disabled={projects.length === 0}
          onChange={(event) => setProjectId(event.currentTarget.value)}
        >
          {projects.length === 0 ? <option value="">{t("connectors.project")}</option> : null}
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
      </div>
      {projects.length === 0 ? <p>{t("connectors.noProjects")}</p> : null}
      {href ? (
        <a className="primary" href={href}>
          {t("connectors.download")}
        </a>
      ) : (
        <button className="primary" type="button" disabled>
          {t("connectors.download")}
        </button>
      )}
    </div>
  );
}


