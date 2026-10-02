import { DeskHome } from "@/components/DeskHome";
import { Offline } from "@/components/Offline";
import { Shell } from "@/components/Shell";
import { requireDesk } from "@/lib/guard";

export default async function HomePage() {
  const desk = await requireDesk();
  if (desk.offline) return <Offline />;
  return (
    <Shell name={desk.name} projects={desk.projects} current="/">
      <DeskHome projects={desk.projects} />
    </Shell>
  );
}
