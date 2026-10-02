"use client";

import { useState } from "react";
import { Notice } from "@/components/Status";
import type { ApiError } from "@/lib/types";

type Locale = { tag: string; language: string; direction: "ltr" | "rtl"; catalogue_status: string; linguistic_review: string };

export function SettingsDesk({
  preferences,
  locales,
  capabilities,
}: {
  preferences: { theme: string; density: string; zone: string };
  locales: Locale[];
  capabilities: { profile: string; sandbox: string; database: string; models: Record<string, string> };
}) {
  const [error, setError] = useState<ApiError | null>(null);
  const [pending, setPending] = useState(false);
  const [saved, setSaved] = useState(false);
  const [locale, setLocale] = useState("en");

  function apply(theme: string, density: string, direction: string, zone: string) {
    const root = document.documentElement;
    const resolved = theme === "system" ? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light") : theme;
    root.dataset.theme = resolved;
    root.dataset.density = density;
    root.dir = direction;
    localStorage.setItem("retrace-theme", theme);
    localStorage.setItem("retrace-density", density);
    localStorage.setItem("retrace-dir", direction);
    localStorage.setItem("retrace-zone", zone);
  }

  return (
    <>
      <p className="eyebrow">{capabilities.profile}</p>
      <h1>Settings</h1>
      <p className="lede">{capabilities.sandbox}</p>
      <p>{capabilities.database}</p>
      <form
        className="panel"
        onSubmit={async (event) => {
          event.preventDefault();
          const data = new FormData(event.currentTarget);
          const theme = String(data.get("theme"));
          const density = String(data.get("density"));
          const zone = String(data.get("zone"));
          const chosen = locales.find((item) => item.tag === locale);
          setPending(true);
          setSaved(false);
          setError(null);
          const response = await fetch("/api/preferences", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ theme, density, zone }),
          });
          const body = (await response.json()) as ApiError;
          setPending(false);
          if (!response.ok) {
            setError(body);
            return;
          }
          apply(theme, density, chosen?.direction ?? "ltr", zone);
          setSaved(true);
        }}
      >
        <div className="field">
          <label htmlFor="theme">Theme</label>
          <select id="theme" name="theme" defaultValue={preferences.theme}>
            <option value="system">Match the system</option>
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="density">Density</label>
          <select id="density" name="density" defaultValue={preferences.density}>
            <option value="comfortable">Comfortable</option>
            <option value="compact">Compact</option>
          </select>
        </div>
        <div className="field">
          <label htmlFor="zone">Clock time zone</label>
          <input id="zone" name="zone" defaultValue={preferences.zone} />
        </div>
        <div className="field">
          <label htmlFor="locale">Locale catalogue</label>
          <select id="locale" value={locale} onChange={(event) => setLocale(event.target.value)}>
            {locales.map((item) => (
              <option key={item.tag} value={item.tag}>
                {item.language} · {item.direction} · {item.catalogue_status}
              </option>
            ))}
          </select>
        </div>
        {locale !== "en" ? (
          <p className="banner" role="status">
            This locale is catalogued and has not had linguistic review. The interface stays in English. The writing direction follows the catalogue, including Urdu as right to left.
          </p>
        ) : null}
        {error?.message ? <Notice message={error.message} next={error.next} /> : null}
        {saved ? <p role="status">Saved on this workstation.</p> : null}
        <button className="primary" type="submit" disabled={pending}>
          {pending ? "Saving…" : "Save settings"}
        </button>
      </form>
      <h2>Models</h2>
      <ul>
        {Object.entries(capabilities.models).map(([name, state]) => (
          <li key={name}>
            {name}: {state}
          </li>
        ))}
      </ul>
    </>
  );
}
