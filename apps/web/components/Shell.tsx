"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { AccountMenu, ThemeToggle } from "@/components/AccountMenu";
import { Clock } from "@/components/Clock";
import { useDesk } from "@/components/DeskProvider";
import type { ProjectBrief } from "@/lib/types";

const NAV = [
  { href: "/", label: "nav.desk" },
  { href: "/wiki", label: "nav.record" },
  { href: "/calendar", label: "nav.calendar" },
  { href: "/connectors", label: "nav.connectors" },
  { href: "/settings", label: "nav.settings" },
];

const GUIDE = [
  { hash: "", href: "/guide", label: "Start here" },
  { hash: "#what", href: "/guide#what", label: "What this desk is for" },
  { hash: "#limits", href: "/guide#limits", label: "What it will not claim" },
  { hash: "#sign-in", href: "/guide#sign-in", label: "Sign in" },
  { hash: "#screen", href: "/guide#screen", label: "Find your way around" },
  { hash: "#account", href: "/guide#account", label: "Theme, language, and clock" },
  { hash: "#case", href: "/guide#case", label: "Open a practice case" },
  { hash: "#project", href: "/guide#project", label: "Work through a project" },
  { hash: "#words", href: "/guide#words", label: "Read a result" },
  { hash: "#record", href: "/guide#record", label: "Write a record" },
  { hash: "#calendar", href: "/guide#calendar", label: "Keep a calendar" },
  { hash: "#connectors", href: "/guide#connectors", label: "Connectors" },
  { hash: "#settings", href: "/guide#settings", label: "Settings" },
  { hash: "#import", href: "/guide#import", label: "Bring in a bundle" },
  { hash: "#trouble", href: "/guide#trouble", label: "If something goes wrong" },
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
  const { t, prefs } = useDesk();
  const pathname = usePathname();
  const [pinned, setPinned] = useState(true);
  const [hover, setHover] = useState(false);
  const [holdClosed, setHoldClosed] = useState(false);
  const [hash, setHash] = useState("");
  const [guideOpen, setGuideOpen] = useState(false);
  const leaveTimer = useRef<number | null>(null);
  const mode = pinned ? "open" : hover && !holdClosed ? "peek" : "closed";
  const shown = mode !== "closed";

  useEffect(() => {
    if (pathname.startsWith("/projects/")) return;
    const key =
      pathname === "/guide"
        ? "nav.guide"
        : pathname === "/wiki"
          ? "nav.record"
          : pathname === "/calendar"
            ? "nav.calendar"
            : pathname === "/connectors"
              ? "nav.connectors"
              : pathname === "/settings"
                ? "nav.settings"
                : "nav.desk";
    document.title = `${t(key)} · RETRACE`;
  }, [pathname, prefs.locale, t]);

  useEffect(() => {
    setHash(window.location.hash);
  }, [pathname]);

  useEffect(() => {
    if (window.localStorage.getItem("retrace-rail") === "closed") setPinned(false);
    if (window.localStorage.getItem("retrace-guide") === "open") setGuideOpen(true);
    return () => {
      if (leaveTimer.current !== null) window.clearTimeout(leaveTimer.current);
    };
  }, []);

  function persist(next: boolean) {
    setPinned(next);
    window.localStorage.setItem("retrace-rail", next ? "open" : "closed");
  }

  function onGuide() {
    setGuideOpen((open) => {
      const next = !open;
      window.localStorage.setItem("retrace-guide", next ? "open" : "closed");
      return next;
    });
  }

  function onToggle() {
    if (pinned) {
      persist(false);
      setHoldClosed(true);
      return;
    }
    setHoldClosed(false);
    persist(true);
  }

  function onEnter() {
    if (leaveTimer.current !== null) window.clearTimeout(leaveTimer.current);
    setHover(true);
  }

  function onLeave() {
    if (leaveTimer.current !== null) window.clearTimeout(leaveTimer.current);
    leaveTimer.current = window.setTimeout(() => {
      setHover(false);
      setHoldClosed(false);
    }, 90);
  }

  return (
    <div className="desk" data-rail={mode}>
      <a className="skip" href="#content">
        {t("nav.skip")}
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
            <span className="brand-kicker">{t("brand.kicker")}</span>
          </span>
        </Link>
        <div className="top-spacer" />
        <Clock />
        <div className="who">
          <ThemeToggle />
          <AccountMenu name={name} />
        </div>
      </header>
      <aside className="rail" onMouseEnter={onEnter} onMouseLeave={onLeave}>
        <button
          type="button"
          className="rail-toggle"
          aria-expanded={shown}
          aria-controls="desk-rail"
          onClick={onToggle}
        >
          <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true">
            <path d="M10 3 5 8l5 5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <span>{pinned ? t("nav.hide") : t("nav.show")}</span>
        </button>
        <div id="desk-rail" className="rail-body">
          <div className="rail-rest" inert={mode === "closed" ? true : undefined}>
            <nav aria-label={t("nav.label")}>
              {NAV.map((item) => (
                <Link key={item.href} href={item.href} aria-current={current === item.href ? "page" : undefined}>
                  {t(item.label)}
                </Link>
              ))}
            </nav>
            <h2 className="guide-heading">
              <button
                type="button"
                className="guide-toggle"
                id="how-to-use"
                aria-expanded={guideOpen}
                aria-controls="guide-links"
                onClick={onGuide}
              >
                <span>{t("nav.guide")}</span>
                <svg width="14" height="14" viewBox="0 0 16 16" aria-hidden="true">
                  <path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </h2>
            <nav id="guide-links" className="guide-nav" aria-labelledby="how-to-use" hidden={!guideOpen}>
              {GUIDE.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  aria-current={pathname === "/guide" && hash === item.hash ? "page" : undefined}
                  onClick={() => setHash(item.hash)}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
            <h2>{t("nav.projects")}</h2>
            {projects.length === 0 ? <p className="missing">{t("nav.empty")}</p> : null}
            {projects.map((project) => (
              <Link className="project-link" key={project.id} href={`/projects/${project.id}`}>
                {project.name}
                <span>{project.discipline || t("nav.imported")}</span>
              </Link>
            ))}
          </div>
        </div>
      </aside>
      <main className="main" id="content">
        {children}
      </main>
    </div>
  );
}
