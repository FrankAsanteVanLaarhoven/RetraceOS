"use client";

import { useEffect, useState } from "react";
import { useDesk } from "@/components/DeskProvider";

export function Clock() {
  const { t, prefs } = useDesk();
  const [now, setNow] = useState<Date | null>(null);
  const [zone, setZone] = useState(prefs.zone || "UTC");

  useEffect(() => {
    function sync() {
      setZone(window.localStorage.getItem("retrace-zone") || prefs.zone || "UTC");
    }
    sync();
    setNow(new Date());
    const timer = window.setInterval(() => setNow(new Date()), 30000);
    window.addEventListener("retrace-preferences", sync);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("retrace-preferences", sync);
    };
  }, [prefs.zone]);

  if (!now) {
    return (
      <div className="clock">
        <strong>UTC</strong>
        <span>{t("clock.loading")}</span>
      </div>
    );
  }

  function format(timeZone: string) {
    const options: Intl.DateTimeFormatOptions = { hour: "2-digit", minute: "2-digit", timeZone, hourCycle: "h23" };
    try {
      return new Intl.DateTimeFormat(prefs.locale, options).format(now);
    } catch {
      return new Intl.DateTimeFormat("en-GB", options).format(now);
    }
  }
  const utc = format("UTC");
  let local = utc;
  let localLabel = "UTC";
  try {
    local = format(zone);
    localLabel = zone;
  } catch {
    localLabel = "UTC";
  }
  const localLine = `${local} ${localLabel}`;
  const utcLine = `${utc} UTC`;
  const same = localLine === utcLine;

  return (
    <div className="clock">
      <strong>{same ? utcLine : localLine}</strong>
      {same ? null : <span>{utcLine}</span>}
    </div>
  );
}
