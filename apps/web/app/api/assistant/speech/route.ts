import { NextRequest } from "next/server";
import { speechSpeed, voiceById, type Tone } from "@/lib/assistant";
import { clientAddress, openRouterConfigured, speak, withinLimit } from "@/lib/openrouter";

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
  if (!withinLimit(clientAddress(request.headers.get("x-forwarded-for")), "speech", 30)) {
    return Response.json(
      { error: "rate_limited", message: "Too many requests from this machine.", next: "Wait a minute and try again." },
      { status: 429, headers: noStore },
    );
  }
  let body: { text?: unknown; voice?: unknown; tone?: unknown };
  try {
    body = (await request.json()) as { text?: unknown; voice?: unknown; tone?: unknown };
  } catch {
    return Response.json(
      { error: "invalid", message: "The spoken reply could not be read.", next: "Try again." },
      { status: 400, headers: noStore },
    );
  }
  const voice = voiceById(typeof body.voice === "string" ? body.voice : "");
  const tone = body.tone;
  const text = typeof body.text === "string" ? body.text.trim().slice(0, 700) : "";
  if (!voice || (tone !== "calm" && tone !== "clear" && tone !== "bright") || !text) {
    return Response.json(
      { error: "invalid", message: "Choose a voice before speaking the reply.", next: "The reply has to contain words." },
      { status: 400, headers: noStore },
    );
  }
  return speak(text, voice.id, speechSpeed(tone as Tone));
}
