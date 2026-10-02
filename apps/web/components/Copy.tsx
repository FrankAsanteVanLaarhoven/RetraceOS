"use client";

import { useEffect } from "react";
import { useDesk } from "@/components/DeskProvider";

export function Copy({ k, className, as: Tag = "span" }: { k: string; className?: string; as?: "p" | "h1" | "h2" | "span" }) {
  const { t } = useDesk();
  return <Tag className={className}>{t(k)}</Tag>;
}

export function ViewTitle({ k }: { k: string }) {
  const { t, prefs } = useDesk();
  useEffect(() => {
    document.title = `${t(k)} · RETRACE`;
  }, [k, prefs.locale, t]);
  return null;
}
