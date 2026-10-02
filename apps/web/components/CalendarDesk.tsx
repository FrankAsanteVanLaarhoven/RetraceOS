"use client";

import { useState } from "react";
import { useDesk } from "@/components/DeskProvider";
import { Notice } from "@/components/Status";
import type { ApiError } from "@/lib/types";

export function CalendarDesk({
  initial,
}: {
  initial: Array<{ id: string; title: string; start_utc: string; zone: string }>;
}) {
  const { t, prefs } = useDesk();
  const [events, setEvents] = useState(initial);
  const [error, setError] = useState<ApiError | null>(null);
  const [pending, setPending] = useState(false);

  return (
    <>
      <p className="eyebrow">{t("calendar.eyebrow")}</p>
      <h1>{t("calendar.title")}</h1>
      <p className="lede">{t("calendar.lede")}</p>
      {error?.message ? <Notice message={error.message} next={error.next} /> : null}
      <form
        className="panel"
        onSubmit={async (event) => {
          event.preventDefault();
          const data = new FormData(event.currentTarget);
          setPending(true);
          setError(null);
          const fold = data.get("fold");
          const response = await fetch("/api/calendar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              title: data.get("title"),
              local_start: data.get("local_start"),
              zone: data.get("zone"),
              fold: fold === "" ? null : Number(fold),
            }),
          });
          const body = (await response.json()) as ApiError & { id?: string; title?: string; start_utc?: string; zone?: string };
          setPending(false);
          if (!response.ok || !body.id) {
            setError(body);
            return;
          }
          setEvents((items) => [...items, { id: body.id!, title: body.title!, start_utc: body.start_utc!, zone: body.zone! }]);
        }}
      >
        <div className="field">
          <label htmlFor="title">{t("calendar.titleField")}</label>
          <input id="title" name="title" required defaultValue={t("calendar.defaultTitle")} />
        </div>
        <div className="field">
          <label htmlFor="local_start">{t("calendar.local")}</label>
          <input id="local_start" name="local_start" required placeholder="2026-11-01T01:30" className="keep-ltr" />
        </div>
        <div className="field">
          <label htmlFor="zone">{t("calendar.zone")}</label>
          <input id="zone" name="zone" required defaultValue={prefs.zone || "Europe/London"} className="keep-ltr" />
        </div>
        <div className="field">
          <label htmlFor="fold">{t("calendar.fold")}</label>
          <select id="fold" name="fold" defaultValue="">
            <option value="">{t("calendar.unspecified")}</option>
            <option value="0">{t("calendar.earlier")}</option>
            <option value="1">{t("calendar.later")}</option>
          </select>
        </div>
        <button className="primary" type="submit" disabled={pending}>
          {pending ? t("calendar.saving") : t("calendar.add")}
        </button>
      </form>
      <ul>
        {events.map((event) => (
          <li key={event.id}>
            {t("calendar.line", { title: event.title, utc: event.start_utc, zone: event.zone })}
          </li>
        ))}
      </ul>
      <p>
        <a href="/api/calendar.ics">Download the calendar as ICS</a>
      </p>
    </>
  );
}
