import type { Metadata } from "next";
import { Offline } from "@/components/Offline";
import { Shell } from "@/components/Shell";
import { WikiDesk } from "@/components/WikiDesk";
import { requireDesk } from "@/lib/guard";

export const metadata: Metadata = { title: "Record" };

export default async function WikiPage() {
  const desk = await requireDesk();
  if (desk.offline) return <Offline />;
  return (
    <Shell name={desk.name} projects={desk.projects} current="/wiki">
      <p className="eyebrow">Project record</p>
      <h1>Record</h1>
      <p className="lede">Pages are assembled from the snapshot, the contract, and the runs. Missing evidence stays an abstention.</p>
      <WikiDesk projects={desk.projects} />
    </Shell>
  );
}
