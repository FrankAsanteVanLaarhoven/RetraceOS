import type { Metadata } from "next";
import { Offline } from "@/components/Offline";
import { SettingsDesk } from "@/components/SettingsDesk";
import { Shell } from "@/components/Shell";
import { requireDesk } from "@/lib/guard";
import { api } from "@/lib/server";

export const metadata: Metadata = { title: "Settings" };

export default async function SettingsPage() {
  const desk = await requireDesk();
  if (desk.offline) return <Offline />;
  const [preferencesResponse, localesResponse, capabilitiesResponse] = await Promise.all([
    api("/api/preferences"),
    api("/api/locales"),
    api("/api/capabilities"),
  ]);
  if (!preferencesResponse?.ok || !localesResponse?.ok || !capabilitiesResponse?.ok) return <Offline />;
  const preferences = (await preferencesResponse.json()) as { theme: string; density: string; zone: string };
  const locales = (await localesResponse.json()) as { locales: Array<{ tag: string; language: string; direction: "ltr" | "rtl"; catalogue_status: string; linguistic_review: string }> };
  const capabilities = (await capabilitiesResponse.json()) as { profile: string; sandbox: string; database: string; models: Record<string, string> };
  return (
    <Shell name={desk.name} projects={desk.projects} current="/settings">
      <SettingsDesk preferences={preferences} locales={locales.locales} capabilities={capabilities} />
    </Shell>
  );
}
