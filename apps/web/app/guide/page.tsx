import type { Metadata } from "next";
import { GuideDesk } from "@/components/GuideDesk";
import { Offline } from "@/components/Offline";
import { Shell } from "@/components/Shell";
import { requireDesk } from "@/lib/guard";

export const metadata: Metadata = { title: "How to use" };

export default async function GuidePage() {
  const desk = await requireDesk();
  if (desk.offline) return <Offline />;
  return (
    <Shell name={desk.name} projects={desk.projects} current="/guide">
      <GuideDesk />
    </Shell>
  );
}
