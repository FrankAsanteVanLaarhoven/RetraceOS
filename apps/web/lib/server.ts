import { cookies } from "next/headers";
import { apiBase } from "@/lib/api-base";

export async function api(path: string): Promise<Response | null> {
  const jar = (await cookies()).toString();
  try {
    return await fetch(`${apiBase()}${path}`, { headers: { cookie: jar }, cache: "no-store" });
  } catch {
    return null;
  }
}
