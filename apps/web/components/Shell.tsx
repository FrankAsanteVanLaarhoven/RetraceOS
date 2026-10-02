import Link from "next/link";
import type { ReactNode } from "react";
import { Clock } from "@/components/Clock";
import { SignOutButton } from "@/components/SignOutButton";
import type { ProjectBrief } from "@/lib/types";

const NAV = [
  { href: "/", label: "Desk" },
  { href: "/wiki", label: "Record" },
  { href: "/calendar", label: "Calendar" },
  { href: "/connectors", label: "Connectors" },
  { href: "/settings", label: "Settings" },
];

export function Shell({
  name,
  projects,
  current,
  children,
}: {
  name: string;
  projects: ProjectBrief[];
  current?: string;
  children: ReactNode;
}) {
  return (
    <div className="desk">
      <a className="skip" href="#content">
        Skip to content
      </a>
      <header className="topbar">
        <Link className="brand" href="/">
          <svg width="28" height="28" viewBox="0 0 32 32" aria-hidden="true">
            <rect width="32" height="32" rx="7" fill="currentColor" />
            <path d="M9 23V9h8.2a5.2 5.2 0 0 1 0 10.4H9" stroke="var(--bg)" fill="none" strokeWidth="1.7" />
            <path d="M15.5 17.2 23 23" stroke="var(--bg)" fill="none" strokeWidth="1.7" />
          </svg>
          <span>
            <span className="brand-name">RETRACE</span>
            <span className="brand-kicker">Evidence desk</span>
          </span>
        </Link>
        <div className="top-spacer" />
        <Clock />
        <div className="who">
          <div>
            <strong>{name}</strong>
            <small>Local session</small>
          </div>
          <SignOutButton />
        </div>
      </header>
      <aside className="rail">
        <nav aria-label="Desk">
          {NAV.map((item) => (
            <Link key={item.href} href={item.href} aria-current={current === item.href ? "page" : undefined}>
              {item.label}
            </Link>
          ))}
        </nav>
        <h2>Projects</h2>
        {projects.length === 0 ? <p className="missing">No open projects.</p> : null}
        {projects.map((project) => (
          <Link className="project-link" key={project.id} href={`/projects/${project.id}`}>
            {project.name}
            <span>{project.discipline || "Imported"}</span>
          </Link>
        ))}
      </aside>
      <main className="main" id="content">
        {children}
      </main>
    </div>
  );
}
