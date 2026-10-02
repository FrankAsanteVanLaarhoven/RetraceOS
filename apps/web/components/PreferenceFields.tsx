"use client";

import { useEffect, useState } from "react";
import { useDesk, type LocaleRow } from "@/components/DeskProvider";
import { Notice } from "@/components/Status";

function localeLabel(item: LocaleRow) {
  if (item.endonym && item.endonym !== item.language) return `${item.endonym} · ${item.language}`;
  return item.endonym || item.language;
}

export function PreferenceFields({ idPrefix }: { idPrefix: string }) {
  const desk = useDesk();
  const { t, prefs, locales, error } = desk;
  const [zone, setZone] = useState(prefs.zone);

  useEffect(() => setZone(prefs.zone), [prefs.zone]);

  return (
    <>
      <div className="field">
        <label htmlFor={`${idPrefix}-theme`}>{t("account.theme")}</label>
        <select id={`${idPrefix}-theme`} value={prefs.theme} onChange={(event) => desk.setTheme(event.target.value)}>
          <option value="system">{t("theme.system")}</option>
          <option value="light">{t("theme.light")}</option>
          <option value="dark">{t("theme.dark")}</option>
        </select>
      </div>
      <div className="field">
        <label htmlFor={`${idPrefix}-density`}>{t("account.density")}</label>
        <select id={`${idPrefix}-density`} value={prefs.density} onChange={(event) => desk.setDensity(event.target.value)}>
          <option value="comfortable">{t("density.comfortable")}</option>
          <option value="compact">{t("density.compact")}</option>
        </select>
      </div>
      <div className="field">
        <label htmlFor={`${idPrefix}-locale`}>{t("account.language")}</label>
        <select id={`${idPrefix}-locale`} value={prefs.locale} onChange={(event) => desk.setLocale(event.target.value)}>
          {locales.map((item) => (
            <option key={item.tag} value={item.tag} lang={item.tag}>
              {localeLabel(item)}
            </option>
          ))}
        </select>
      </div>
      <div className="field">
        <label htmlFor={`${idPrefix}-zone`}>{t("account.zone")}</label>
        <input
          id={`${idPrefix}-zone`}
          value={zone}
          autoComplete="off"
          spellCheck={false}
          onChange={(event) => setZone(event.target.value)}
          onBlur={(event) => {
            const next = event.currentTarget.value.trim();
            if (next && next !== prefs.zone) desk.setZone(next);
          }}
          onKeyDown={(event) => {
            if (event.key !== "Enter") return;
            event.preventDefault();
            const next = event.currentTarget.value.trim();
            if (next && next !== prefs.zone) desk.setZone(next);
          }}
        />
      </div>
      {prefs.locale !== "en" ? (
        <p className="banner" role="status">
          {t("account.draft")}
        </p>
      ) : null}
      {error?.message ? <Notice message={error.message} next={error.next} /> : null}
    </>
  );
}
