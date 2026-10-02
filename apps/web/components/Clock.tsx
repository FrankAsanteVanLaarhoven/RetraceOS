"use client";

import { useEffect, useState } from "react";

export function Clock() {
  const [now, setNow] = useState<Date | null>(null);
  const [zone, setZone] = useState("UTC");

  useEffect(() => {
    const stored = window.localStorage.getItem("retrace-zone") || "UTC";
    setZone(stored);
    setNow(new Date());
    const timer = window.setInterval(() => setNow(new Date()), 30000);
    return () => window.clearInterval(timer);
  }, []);

  if (!now) {
    return (
      <div className="clock">
        <strong>UTC</strong>
        <span>Loading the clock</span>
      </div>
    );
  }

  const utc = new Intl.DateTimeFormat("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
    hourCycle: "h23",
  }).format(now);
  let local = utc;
  let localLabel = "UTC";
  try {
    local = new Intl.DateTimeFormat("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: zone,
      hourCycle: "h23",
    }).format(now);
    localLabel = zone;
  } catch {
    localLabel = "UTC";
  }

  return (
    <div className="clock">
      <strong>
        {local} {localLabel}
      </strong>
      <span>{utc} UTC</span>
    </div>
  );
}
