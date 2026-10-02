import { cookies } from "next/headers";

const API = process.env.RETRACE_API ?? "http://127.0.0.1:8765";

export async function api(path: string): Promise<Response | null> {
  const jar = (await cookies()).toString();
  try {
    return await fetch(`${API}${path}`, { headers: { cookie: jar }, cache: "no-store" });
  } catch {
    return null;
  }
}
