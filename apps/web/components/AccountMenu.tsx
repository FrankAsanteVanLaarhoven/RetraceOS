"use client";

import { useEffect, useId, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { PreferenceFields } from "@/components/PreferenceFields";
import { useDesk } from "@/components/DeskProvider";

export function ThemeToggle() {
  const { t, resolvedTheme, toggleTheme } = useDesk();
  const toDark = resolvedTheme !== "dark";
  return (
    <button type="button" className="icon-button" aria-label={toDark ? t("theme.toDark") : t("theme.toLight")} onClick={toggleTheme}>
      {toDark ? (
        <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
          <path d="M12.2 11.6A4.8 4.8 0 0 1 6.4 5.8 4.2 4.2 0 1 0 12.2 11.6Z" fill="none" stroke="currentColor" strokeWidth="1.4" />
        </svg>
      ) : (
        <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
          <circle cx="9" cy="9" r="2.4" fill="none" stroke="currentColor" strokeWidth="1.4" />
          <path d="M9 2.2v1.6M9 14.2v1.6M2.2 9h1.6M14.2 9h1.6M4.2 4.2l1.1 1.1M12.7 12.7l1.1 1.1M13.8 4.2l-1.1 1.1M5.3 12.7l-1.1 1.1" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
      )}
    </button>
  );
}

export function AccountMenu({ name }: { name: string }) {
  const { t } = useDesk();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuId = useId();

  useEffect(() => {
    if (!open) return;
    document.getElementById("account-theme")?.focus();
    function onPointer(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
        buttonRef.current?.focus();
      }
    }
    function onKey(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      setOpen(false);
      buttonRef.current?.focus();
    }
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="account" ref={rootRef}>
      <button
        ref={buttonRef}
        type="button"
        className="account-button"
        aria-expanded={open}
        aria-haspopup="dialog"
        aria-controls={menuId}
        onClick={() => setOpen((value) => !value)}
      >
        <span>
          <strong>{name}</strong>
          <small>{t("account.session")}</small>
        </span>
        <svg width="14" height="14" viewBox="0 0 14 14" aria-hidden="true">
          <path d="M3 5.2 7 9l4-3.8" fill="none" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </button>
      {open ? (
        <div id={menuId} className="account-menu" role="dialog" aria-label={t("account.open")}>
          <PreferenceFields idPrefix="account" />
          <button
            className="ghost account-signout"
            type="button"
            onClick={async () => {
              await fetch("/api/session", { method: "DELETE" });
              router.push("/login");
              router.refresh();
            }}
          >
            {t("account.signOut")}
          </button>
        </div>
      ) : null}
    </div>
  );
}
