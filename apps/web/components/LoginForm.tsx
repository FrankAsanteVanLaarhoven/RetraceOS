"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useDesk } from "@/components/DeskProvider";
import { Notice } from "@/components/Status";
import type { ApiError } from "@/lib/types";

export function LoginForm() {
  const router = useRouter();
  const { t, prefs } = useDesk();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

  useEffect(() => {
    document.title = `${t("login.title")} · RETRACE`;
  }, [prefs.locale, t]);

  return (
    <div className="login">
      <form
        className="login-card"
        onSubmit={async (event) => {
          event.preventDefault();
          const data = new FormData(event.currentTarget);
          setPending(true);
          setError(null);
          const response = await fetch("/api/session", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ display_name: data.get("display_name") }),
          });
          const body = (await response.json()) as ApiError;
          setPending(false);
          if (!response.ok) {
            setError(body);
            return;
          }
          router.push("/");
          router.refresh();
        }}
      >
        <p className="eyebrow">{t("login.eyebrow")}</p>
        <h1>{t("login.title")}</h1>
        <p className="lede">{t("login.lede")}</p>
        <div className="field">
          <label htmlFor="display_name">{t("login.name")}</label>
          <input id="display_name" name="display_name" autoComplete="name" required maxLength={40} />
        </div>
        {error?.message ? <Notice message={error.message} next={error.next} /> : null}
        <button className="primary" type="submit" disabled={pending}>
          {pending ? t("login.pending") : t("login.continue")}
        </button>
      </form>
    </div>
  );
}
