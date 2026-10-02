import type { Metadata } from "next";
import { CalendarDesk } from "@/components/CalendarDesk";
import { Offline } from "@/components/Offline";
import { Shell } from "@/components/Shell";
import { requireDesk } from "@/lib/guard";
import { api } from "@/lib/server";

export const metadata: Metadata = { title: "Calendar" };

export default async function CalendarPage() {
  const desk = await requireDesk();
  if (desk.offline) return <Offline />;
  const response = await api("/api/calendar");
  const events = response?.ok ? ((await response.json()) as { events: Array<{ id: string; title: string; start_utc: string; zone: string }> }).events : [];
  return (
    <Shell name={desk.name} projects={desk.projects} current="/calendar">
      <CalendarDesk initial={events} />
    </Shell>
  );
}
