"use client";

import { useDesk } from "@/components/DeskProvider";
import { statusLabel, statusMark } from "@/lib/types";

export function Outcome({ status, heading = false }: { status: string; heading?: boolean }) {
  const { t } = useDesk();
  const key = `status.${status}`;
  const translated = t(key);
  const label = translated === key ? statusLabel(status) : translated;
  const Tag = heading ? "h2" : "p";
  return (
    <Tag className={`outcome s-${status}`}>
      <i aria-hidden="true">{statusMark(status)}</i>
      <span>{label}</span>
    </Tag>
  );
}

export function Notice({ message, next }: { message: string; next?: string }) {
  return (
    <div className="notice" role="alert">
      <strong>{message}</strong>
      {next ? <span>{next}</span> : null}
    </div>
  );
}
