import type { Metadata } from "next";
import { ConnectorsDesk } from "@/components/ConnectorsDesk";
import { Offline } from "@/components/Offline";
import { Shell } from "@/components/Shell";
import { requireDesk } from "@/lib/guard";
import { api } from "@/lib/server";

export const metadata: Metadata = { title: "Connectors" };

export default async function ConnectorsPage() {
  const desk = await requireDesk();
  if (desk.offline) return <Offline />;
  const response = await api("/api/connectors");
  const body = response?.ok ? ((await response.json()) as { connectors: Array<{ id: string; status: string; detail: string }> }) : { connectors: [] };
  return (
    <Shell name={desk.name} projects={desk.projects} current="/connectors">
      <ConnectorsDesk connectors={body.connectors} projects={desk.projects.map((project) => ({ id: project.id, name: project.name }))} />
    </Shell>
  );
}
