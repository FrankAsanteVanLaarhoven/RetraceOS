"use client";

import { useState } from "react";
import { Notice } from "@/components/Status";
import type { ApiError } from "@/lib/types";

export function CalendarDesk({
  initial,
}: {
  initial: Array<{ id: string; title: string; start_utc: string; zone: string }>;
}) {
  const [events, setEvents] = useState(initial);
  const [error, setError] = useState<ApiError | null>(null);
  const [pending, setPending] = useState(false);

  return (
    <>
      <p className="eyebrow">Internal schedule</p>
      <h1>Calendar</h1>
      <p className="lede">
        Times are stored in UTC. Google Calendar is not connected. If a local time happens twice, RETRACE asks which instant you mean.
      </p>
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
          <label htmlFor="title">Title</label>
          <input id="title" name="title" required defaultValue="Review the repair" />
        </div>
        <div className="field">
          <label htmlFor="local_start">Local time</label>
          <input id="local_start" name="local_start" required placeholder="2026-11-01T01:30" />
        </div>
        <div className="field">
          <label htmlFor="zone">Time zone</label>
          <input id="zone" name="zone" required defaultValue="Europe/London" />
        </div>
        <div className="field">
          <label htmlFor="fold">Fold, if the hour repeats</label>
          <select id="fold" name="fold" defaultValue="">
            <option value="">Not specified</option>
            <option value="0">Earlier instant</option>
            <option value="1">Later instant</option>
          </select>
        </div>
        <button className="primary" type="submit" disabled={pending}>
          {pending ? "Saving…" : "Add to the internal calendar"}
        </button>
      </form>
      <ul>
        {events.map((event) => (
          <li key={event.id}>
            {event.title} · {event.start_utc} UTC · organised in {event.zone}
          </li>
        ))}
      </ul>
      <p>
        <a href="/api/calendar.ics">Download the calendar as ICS</a>
      </p>
    </>
  );
}
