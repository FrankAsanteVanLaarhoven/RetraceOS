import { NextRequest } from "next/server";

const API = process.env.RETRACE_API ?? "http://127.0.0.1:8765";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = new URL(`${API}/api/${path.join("/")}`);
  target.search = request.nextUrl.search;
  const headers = new Headers();
  const cookie = request.headers.get("cookie");
  if (cookie) headers.set("cookie", cookie);
  headers.set("origin", request.headers.get("origin") ?? "http://127.0.0.1:3011");
  const contentType = request.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);
  const hasBody = request.method !== "GET" && request.method !== "HEAD";
  const response = await fetch(target, {
    method: request.method,
    headers,
    body: hasBody ? await request.arrayBuffer() : undefined,
    redirect: "manual",
  });
  const outgoing = new Headers();
  response.headers.forEach((value, key) => {
    const lower = key.toLowerCase();
    if (lower === "content-encoding" || lower === "content-length" || lower === "set-cookie") return;
    outgoing.set(key, value);
  });
  for (const setCookie of response.headers.getSetCookie()) outgoing.append("set-cookie", setCookie);
  return new Response(await response.arrayBuffer(), { status: response.status, headers: outgoing });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
