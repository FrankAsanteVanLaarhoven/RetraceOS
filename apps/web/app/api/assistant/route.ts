import { NextRequest } from "next/server";
import { cleanTurns, jobById } from "@/lib/assistant";
import { assistantCatalogue, clientAddress, openRouterConfigured, streamReply, withinLimit } from "@/lib/openrouter";

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

function limited() {
  return Response.json(
    { error: "rate_limited", message: "Too many requests from this machine.", next: "Wait a minute and try again." },
    { status: 429, headers: noStore },
  );
}

export async function GET() {
  return Response.json(assistantCatalogue(), { headers: noStore });
}

export async function POST(request: NextRequest) {
  if (!openRouterConfigured()) return missing();
  if (!withinLimit(clientAddress(request.headers.get("x-forwarded-for")), "talk", 20)) return limited();
  let body: { job?: unknown; messages?: unknown };
  try {
    body = (await request.json()) as { job?: unknown; messages?: unknown };
  } catch {
    return Response.json(
      { error: "invalid", message: "The message could not be read.", next: "Send the conversation as text." },
      { status: 400, headers: noStore },
    );
  }
  const job = jobById(typeof body.job === "string" ? body.job : "");
  const turns = cleanTurns(body.messages);
  if (!job || !turns) {
    return Response.json(
      {
        error: "invalid",
        message: "Choose a job and write a message.",
        next: "The last line has to be yours, and a turn stays under 2,000 characters.",
      },
      { status: 400, headers: noStore },
    );
  }
  return streamReply(job, turns);
}
