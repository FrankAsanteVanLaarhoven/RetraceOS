import { redirect } from "next/navigation";
import { api } from "@/lib/server";
import type { ProjectBrief } from "@/lib/types";

export async function requireDesk(): Promise<
  { offline: true } | { offline: false; name: string; projects: ProjectBrief[] }
> {
  const sessionResponse = await api("/api/session");
  if (!sessionResponse) return { offline: true };
  if (sessionResponse.status === 401) redirect("/login");
  const session = (await sessionResponse.json()) as { display_name: string };
  const projectsResponse = await api("/api/projects");
  const projects = projectsResponse?.ok ? ((await projectsResponse.json()) as { projects: ProjectBrief[] }).projects : [];
  return { offline: false, name: session.display_name, projects };
}
