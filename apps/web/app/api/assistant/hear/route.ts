import { NextRequest } from "next/server";
import { clientAddress, hear, openRouterConfigured, withinLimit } from "@/lib/openrouter";

export const dynamic = "force-dynamic";

const noStore = { "Cache-Control": "no-store" };

function missing() {
  return Response.json(
    {
      error: "needs_configuration",
      message: "The OpenRouter key is not set on this server. Add OPENROUTER_API_KEY in the Vercel environment, then reload.",
      next: "Nothing was sent.",
    },
    { status: 503, headers: noStore },
  );
}

export async function POST(request: NextRequest) {
  if (!openRouterConfigured()) return missing();
  if (!withinLimit(clientAddress(request.headers.get("x-forwarded-for")), "hear", 20)) {
    return Response.json(
      { error: "rate_limited", message: "Too many requests from this machine.", next: "Wait a minute and try again." },
      { status: 429, headers: noStore },
    );
  }
  let body: { audio?: unknown; format?: unknown; language?: unknown };
  try {
    body = (await request.json()) as { audio?: unknown; format?: unknown; language?: unknown };
  } catch {
    return Response.json(
      { error: "invalid", message: "The recording could not be read.", next: "Try a shorter turn, or type the message." },
      { status: 400, headers: noStore },
    );
  }
  const format = body.format;
  const language = body.language;
  const audio = typeof body.audio === "string" ? body.audio : "";
  const formatOk = format === "webm" || format === "wav" || format === "mp3";
  const languageOk = language === "en" || language === "fr";
  const audioOk = audio.length >= 16 && audio.length <= 2_000_000 && /^[A-Za-z0-9+/]+={0,2}$/.test(audio);
  if (!formatOk || !languageOk || !audioOk) {
    return Response.json(
      {
        error: "invalid",
        message: "That recording could not be accepted.",
        next: "Speak a shorter turn, or type the message.",
      },
      { status: 400, headers: noStore },
    );
  }
  const result = await hear(audio, format, language);
  if ("error" in result) {
    return Response.json(
      { error: "hear", message: result.error, next: "Try again, or type the message." },
      { status: 502, headers: noStore },
    );
  }
  return Response.json({ text: result.text }, { headers: noStore });
}
