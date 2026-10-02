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
      <WikiDesk projects={desk.projects} />
    </Shell>
  );
}
