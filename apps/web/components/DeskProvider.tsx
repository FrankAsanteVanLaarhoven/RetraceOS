"use client";

import { usePathname } from "next/navigation";
import { createContext, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import catalogue from "@/lib/catalogue.json";
import { loadLocale, translate } from "@/lib/i18n";
import type { ApiError } from "@/lib/types";

export type LocaleRow = {
  tag: string;
  language: string;
  endonym?: string;
  direction: "ltr" | "rtl";
  catalogue_status: string;
  linguistic_review: string;
};

export type Prefs = { theme: string; density: string; zone: string; locale: string };

type Desk = {
  prefs: Prefs;
  resolvedTheme: "light" | "dark";
  locales: LocaleRow[];
  error: ApiError | null;
  t: (key: string, vars?: Record<string, string>) => string;
  setTheme: (theme: string) => void;
  toggleTheme: () => void;
  setDensity: (density: string) => void;
  setLocale: (locale: string) => void;
  setZone: (zone: string) => void;
};

const DeskContext = createContext<Desk | null>(null);
const bootCatalogue = catalogue as LocaleRow[];
const PREF_KEYS = ["theme", "density", "zone", "locale"] as const;

function mergeSaved(server: Prefs, baseline: Prefs, edited: Prefs): Prefs {
  const next = { ...server };
  for (const key of PREF_KEYS) {
    if (edited[key] !== baseline[key]) next[key] = edited[key];
  }
  return next;
}

function readLocal(): Prefs {
  const theme = localStorage.getItem("retrace-theme") || "system";
  const density = localStorage.getItem("retrace-density") || "comfortable";
  const zone = localStorage.getItem("retrace-zone") || "UTC";
  const locale = localStorage.getItem("retrace-locale") || "en";
  return {
    theme: theme === "light" || theme === "dark" || theme === "system" ? theme : "system",
    density: density === "compact" ? "compact" : "comfortable",
    zone,
    locale,
  };
}

function directionFor(locale: string, locales: LocaleRow[]): "ltr" | "rtl" {
  const row = locales.find((item) => item.tag === locale);
  if (row?.direction === "rtl" || row?.direction === "ltr") return row.direction;
  return "ltr";
}

function resolvedTheme(theme: string): "light" | "dark" {
  if (theme === "dark" || theme === "light") return theme;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function applyPrefs(prefs: Prefs, locales: LocaleRow[]) {
  const root = document.documentElement;
  root.dataset.theme = resolvedTheme(prefs.theme);
  root.dataset.themeChoice = prefs.theme;
  root.dataset.density = prefs.density;
  root.lang = prefs.locale || "en";
  root.dir = directionFor(prefs.locale, locales);
  localStorage.setItem("retrace-theme", prefs.theme);
  localStorage.setItem("retrace-density", prefs.density);
  localStorage.setItem("retrace-zone", prefs.zone);
  localStorage.setItem("retrace-locale", prefs.locale);
  localStorage.setItem("retrace-dir", root.dir);
  window.dispatchEvent(new Event("retrace-preferences"));
}

function preferenceError(body: ApiError, locale: string): ApiError {
  const t = (key: string) => translate(locale, key);
  if (body.error === "bad_zone") return { error: body.error, message: t("account.zoneError"), next: t("account.zoneNext") };
  if (body.error === "bad_preference") return { error: body.error, message: t("account.prefError"), next: t("account.prefNext") };
  if (body.error === "bad_locale") return { error: body.error, message: t("account.localeError"), next: t("account.localeNext") };
  return body;
}

export function DeskProvider({ children }: { children: ReactNode }) {
  const [prefs, setPrefs] = useState<Prefs>({ theme: "system", density: "comfortable", zone: "UTC", locale: "en" });
  const [locales, setLocales] = useState<LocaleRow[]>(bootCatalogue);
  const [error, setError] = useState<ApiError | null>(null);
  const [pack, setPack] = useState(0);
  const [themeNow, setThemeNow] = useState<"light" | "dark">("light");
  const prefsRef = useRef(prefs);
  const localesRef = useRef(locales);
  const seq = useRef(0);
  const hydrated = useRef(false);
  const baseline = useRef<Prefs | null>(null);
  const pending = useRef<Prefs | null>(null);
  const signedLoad = useRef(false);
  const commitRef = useRef<(next: Prefs) => void>(() => {});
  const pathname = usePathname();
  prefsRef.current = prefs;
  localesRef.current = locales;

  useEffect(() => {
    const local = readLocal();
    baseline.current = local;
    setPrefs(local);
    setThemeNow(resolvedTheme(local.theme));
    let cancelled = false;
    void loadLocale(local.locale).then(() => {
      if (!cancelled) setPack((value) => value + 1);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (pathname === "/login" || signedLoad.current) return;
    let cancelled = false;
    void (async () => {
      const [localeResponse, preferenceResponse] = await Promise.all([fetch("/api/locales"), fetch("/api/preferences")]);
      if (cancelled) return;
      let nextLocales = localesRef.current;
      if (localeResponse.ok) {
        const body = (await localeResponse.json()) as { locales: LocaleRow[] };
        nextLocales = body.locales;
        setLocales(nextLocales);
        localesRef.current = nextLocales;
      }
      if (!preferenceResponse.ok) {
        hydrated.current = true;
        return;
      }
      const body = (await preferenceResponse.json()) as Partial<Prefs> & { signed_in?: boolean };
      if (cancelled || body.signed_in === false) return;
      signedLoad.current = true;
      const server: Prefs = {
        theme: body.theme || "system",
        density: body.density || "comfortable",
        zone: body.zone || "UTC",
        locale: body.locale || "en",
      };
      const edited = pending.current;
      const next = edited ? mergeSaved(server, baseline.current ?? server, edited) : server;
      pending.current = null;
      hydrated.current = true;
      applyPrefs(next, nextLocales);
      setPrefs(next);
      setThemeNow(resolvedTheme(next.theme));
      const stamp = seq.current;
      void loadLocale(next.locale).then(() => {
        if (!cancelled && seq.current === stamp) setPack((value) => value + 1);
      });
      if (edited && PREF_KEYS.some((key) => next[key] !== server[key])) commitRef.current(next);
    })();
    return () => {
      cancelled = true;
    };
  }, [pathname]);

  useEffect(() => {
    if (prefs.theme !== "system") return;
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    const onChange = () => {
      applyPrefs(prefsRef.current, localesRef.current);
      setThemeNow(resolvedTheme("system"));
    };
    media.addEventListener("change", onChange);
    return () => media.removeEventListener("change", onChange);
  }, [prefs.theme]);

  async function commit(next: Prefs) {
    if (!hydrated.current) {
      pending.current = next;
      applyPrefs(next, localesRef.current);
      setPrefs(next);
      setThemeNow(resolvedTheme(next.theme));
      return;
    }
    const previous = prefsRef.current;
    const id = ++seq.current;
    await loadLocale(next.locale);
    applyPrefs(next, localesRef.current);
    setPrefs(next);
    setThemeNow(resolvedTheme(next.theme));
    setPack((value) => value + 1);
    const response = await fetch("/api/preferences", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(next),
    });
    if (id !== seq.current) return;
    if (response.status === 401) {
      setError(null);
      return;
    }
    if (!response.ok) {
      const body = (await response.json().catch(() => ({}))) as ApiError;
      applyPrefs(previous, localesRef.current);
      setPrefs(previous);
      setThemeNow(resolvedTheme(previous.theme));
      setError(preferenceError(body, previous.locale));
      return;
    }
    setError(null);
  }

  commitRef.current = (next) => {
    void commit(next);
  };

  const value = useMemo<Desk>(() => {
    return {
      prefs,
      resolvedTheme: themeNow,
      locales,
      error,
      t: (key, vars) => translate(prefs.locale, key, vars),
      setTheme: (theme) => void commit({ ...prefsRef.current, theme }),
      toggleTheme: () => {
        const current = prefsRef.current;
        const next = resolvedTheme(current.theme) === "dark" ? "light" : "dark";
        void commit({ ...current, theme: next });
      },
      setDensity: (density) => void commit({ ...prefsRef.current, density }),
      setLocale: (locale) => void commit({ ...prefsRef.current, locale }),
      setZone: (zone) => void commit({ ...prefsRef.current, zone }),
    };
    // pack changes after a catalog loads so visible copy updates.
  }, [prefs, locales, error, themeNow, pack]);

  return <DeskContext.Provider value={value}>{children}</DeskContext.Provider>;
}

export function useDesk() {
  const value = useContext(DeskContext);
  if (!value) throw new Error("useDesk requires DeskProvider");
  return value;
}
