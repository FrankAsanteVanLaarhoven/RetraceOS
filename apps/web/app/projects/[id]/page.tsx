import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Offline } from "@/components/Offline";
import { Shell } from "@/components/Shell";
import { Studio } from "@/components/Studio";
import { requireDesk } from "@/lib/guard";
import { api } from "@/lib/server";
import type { ProjectView } from "@/lib/types";

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const { id } = await params;
  const response = await api(`/api/projects/${id}`);
  if (!response?.ok) return { title: "Project" };
  const view = (await response.json()) as ProjectView;
  const title = `${view.project.name} · RETRACE`;
  return { title: { absolute: title }, description: view.project.question || "A RETRACE project on this workstation." };
}

export default async function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const desk = await requireDesk();
  if (desk.offline) return <Offline />;
  const { id } = await params;
  const response = await api(`/api/projects/${id}`);
  if (!response) return <Offline />;
  if (response.status === 404) notFound();
  if (!response.ok) notFound();
  const view = (await response.json()) as ProjectView;
  return (
    <Shell name={desk.name} projects={desk.projects} current={`/projects/${id}`}>
      <Studio initial={view} />
    </Shell>
  );
}
