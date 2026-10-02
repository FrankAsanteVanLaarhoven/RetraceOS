"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Notice } from "@/components/Status";
import type { ApiError } from "@/lib/types";

export function LoginForm() {
  const router = useRouter();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ApiError | null>(null);

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
        <p className="eyebrow">Local workstation</p>
        <h1>Sign in</h1>
        <p className="lede">
          Enter the name that should appear on reviews. This is not institutional sign-in. Anyone who can open this address on the machine can choose a name.
        </p>
        <div className="field">
          <label htmlFor="display_name">Display name</label>
          <input id="display_name" name="display_name" autoComplete="name" required maxLength={40} />
        </div>
        {error?.message ? <Notice message={error.message} next={error.next} /> : null}
        <button className="primary" type="submit" disabled={pending}>
          {pending ? "Signing in…" : "Continue"}
        </button>
      </form>
    </div>
  );
}
