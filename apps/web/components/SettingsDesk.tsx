"use client";

import { PreferenceFields } from "@/components/PreferenceFields";
import { useDesk } from "@/components/DeskProvider";

export function SettingsDesk({
  capabilities,
}: {
  capabilities: { profile: string; sandbox: string; database: string; models: Record<string, string> };
}) {
  const { t } = useDesk();
  return (
    <>
      <p className="eyebrow">{t("settings.profile")}</p>
      <h1>{t("settings.title")}</h1>
      <p className="lede">{t("settings.sandbox")}</p>
      <p>{t("settings.database")}</p>
      <p>{t("settings.personal")}</p>
      <div className="panel">
        <PreferenceFields idPrefix="settings" />
      </div>
      <h2>{t("settings.models")}</h2>
      <ul>
        {Object.entries(capabilities.models)
          .filter(([name]) => name !== "note")
          .map(([name, state]) => (
            <li key={name}>
              {name === "repairs" ? t("settings.repairsLabel") : name}: {name === "repairs" ? state : state === "CONFIGURED_NOT_USED" ? t("settings.configured") : state === "NEEDS_CONFIGURATION" ? t("settings.needs") : state}
            </li>
          ))}
      </ul>
      <p>{t("settings.modelNote")}</p>
    </>
  );
}
