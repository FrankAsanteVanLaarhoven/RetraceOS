import type { Metadata } from "next";
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
      <p className="eyebrow">Integrations</p>
      <h1>Connectors</h1>
      <p className="lede">Nothing here is connected. A missing credential stays visible. It is not shown as a successful link.</p>
      <div className="cards">
        {body.connectors.map((connector) => (
          <article className="card" key={connector.id}>
            <div className="index">{connector.id}</div>
            <h2>{connector.status}</h2>
            <p>{connector.detail}</p>
          </article>
        ))}
      </div>
    </Shell>
  );
}
