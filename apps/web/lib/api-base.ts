export function apiBase(): string {
  return (process.env.RETRACE_API ?? "http://127.0.0.1:8765").replace(/\/$/, "");
}

export function deskOrigin(): string {
  const host = (process.env.VERCEL_PROJECT_PRODUCTION_URL || process.env.VERCEL_URL || "").trim().replace(/\/$/, "");
  if (!host) return "http://127.0.0.1:3011";
  if (host.startsWith("https://") || host.startsWith("http://")) return host;
  return `https://${host}`;
}
