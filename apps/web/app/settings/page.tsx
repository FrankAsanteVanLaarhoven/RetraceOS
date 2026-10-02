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
  const capabilitiesResponse = await api("/api/capabilities");
  if (!capabilitiesResponse?.ok) return <Offline />;
  const capabilities = (await capabilitiesResponse.json()) as { profile: string; sandbox: string; database: string; models: Record<string, string> };
  return (
    <Shell name={desk.name} projects={desk.projects} current="/settings">
      <SettingsDesk capabilities={capabilities} />
    </Shell>
  );
}
