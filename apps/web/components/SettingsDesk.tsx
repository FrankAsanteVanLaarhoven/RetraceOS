"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PreferenceFields } from "@/components/PreferenceFields";
import { Notice } from "@/components/Status";
import { useDesk } from "@/components/DeskProvider";
import type { ApiError } from "@/lib/types";

export function SettingsDesk({
  name,
  capabilities,
}: {
  name: string;
  capabilities: { profile: string; sandbox: string; database: string; models: Record<string, string> };
}) {
  const { t } = useDesk();
  const router = useRouter();
  const [confirm, setConfirm] = useState("");
  const [pending, setPending] = useState<"export" | "delete" | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [assistant, setAssistant] = useState<{ configured: boolean; standardModel: string } | null>(null);
  useEffect(() => {
    let gone = false;
    fetch("/api/assistant")
      .then((response) => response.json())
      .then((body: { configured?: boolean; standardModel?: string }) => {
        if (!gone) setAssistant({ configured: Boolean(body.configured), standardModel: body.standardModel ?? "" });
      })
      .catch(() => {
        if (!gone) setAssistant({ configured: false, standardModel: "" });
      });
    return () => {
      gone = true;
    };
  }, []);
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
      <p role="status">
        {assistant === null
          ? t("talk.checking")
          : assistant.configured
            ? `${t("talk.title")}: ${assistant.standardModel}`
            : t("talk.needs")}
      </p>
      <h2>{t("settings.privacyTitle")}</h2>
      <p>{t("settings.privacyLede")}</p>
      <p>
        <a className="text-link" href="/privacy">
          {t("login.privacy")}
        </a>
      </p>
      {error?.message ? <Notice message={error.message} next={error.next} /> : null}
      <div className="actions">
        <button
          className="primary"
          type="button"
          disabled={pending !== null}
          onClick={async () => {
            setPending("export");
            setError(null);
            const response = await fetch("/api/account/export");
            if (!response.ok) {
              const body = (await response.json()) as ApiError;
              setError(body.message ? body : { error: "export", message: t("settings.exportError"), next: t("settings.exportNext") });
              setPending(null);
              return;
            }
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = "retrace-record.json";
            link.click();
            URL.revokeObjectURL(url);
            setPending(null);
          }}
        >
          {pending === "export" ? t("settings.exporting") : t("settings.export")}
        </button>
      </div>
      <div className="field">
        <label htmlFor="privacy-confirm">{t("settings.deleteLabel")}</label>
        <input id="privacy-confirm" value={confirm} onChange={(event) => setConfirm(event.target.value)} autoComplete="off" />
      </div>
      <button
        className="ghost"
        type="button"
        disabled={pending !== null || confirm !== name}
        onClick={async () => {
          setPending("delete");
          setError(null);
          const response = await fetch("/api/account", { method: "DELETE" });
          if (!response.ok) {
            const body = (await response.json().catch(() => null)) as ApiError | null;
            setError(body?.message ? body : { error: "delete", message: t("settings.deleteError"), next: t("settings.deleteNext") });
            setPending(null);
            return;
          }
          router.push("/login");
          router.refresh();
        }}
      >
        {pending === "delete" ? t("settings.deleting") : t("settings.delete")}
      </button>
    </>
  );
}
