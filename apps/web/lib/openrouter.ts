import { HEAR_MODEL, JOBS, SPEECH_MODEL, VOICES, type Job, type Turn, systemPrompt } from "@/lib/assistant";

const HITS = new Map<string, number[]>();

export function openRouterConfigured(): boolean {
  return Boolean(process.env.OPENROUTER_API_KEY?.trim());
}

export function assistantCatalogue() {
  return {
    configured: openRouterConfigured(),
    standardModel: JOBS[0].model,
    jobs: JOBS.map((job) => ({ id: job.id, label: job.label, model: job.model, purpose: job.purpose })),
    speechModel: SPEECH_MODEL,
    hearModel: HEAR_MODEL,
    voices: VOICES.map((voice) => ({
      id: voice.id,
      name: voice.name,
      gender: voice.gender,
      country: voice.country,
      tone: voice.tone,
      style: voice.style,
    })),
  };
}

function allow(key: string, limit: number): boolean {
  const now = Date.now();
  const bucket = (HITS.get(key) ?? []).filter((stamp) => now - stamp < 60_000);
  if (bucket.length >= limit) {
    HITS.set(key, bucket);
    return false;
  }
  bucket.push(now);
  HITS.set(key, bucket);
  return true;
}

export function clientAddress(header: string | null): string {
  const first = header?.split(",")[0]?.trim() ?? "local";
  return first.slice(0, 64) || "local";
}

export function withinLimit(address: string, bucket: string, limit: number): boolean {
  return allow(`${bucket}:${address}`, limit);
}

function key(): string {
  return process.env.OPENROUTER_API_KEY?.trim() ?? "";
}

async function postOpenRouter(path: string, body: unknown): Promise<Response> {
  return fetch(`https://openrouter.ai/api/v1/${path}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${key()}`,
      "Content-Type": "application/json",
      "HTTP-Referer": "http://127.0.0.1:3011",
      "X-Title": "RETRACE",
    },
    body: JSON.stringify(body),
  });
}

export function safeProviderMessage(status: number): string {
  if (status === 401 || status === 403) return "OpenRouter refused the server key. Check OPENROUTER_API_KEY in the Vercel environment.";
  if (status === 402) return "OpenRouter could not complete that call because the account has no credit.";
  if (status === 429) return "OpenRouter is limiting calls. Wait a minute and try again.";
  return "OpenRouter could not complete that call. Try again in a moment.";
}

export async function streamReply(job: Job, turns: Turn[]): Promise<Response> {
  const upstream = await postOpenRouter("chat/completions", {
    model: job.model,
    stream: true,
    max_tokens: 400,
    messages: [{ role: "system", content: systemPrompt(job) }, ...turns],
  });
  if (!upstream.ok || !upstream.body) {
    return Response.json({ error: "provider", message: safeProviderMessage(upstream.status), next: "Try again in a moment." }, { status: 502 });
  }
  const encoder = new TextEncoder();
  const decoder = new TextDecoder();
  let buffer = "";
  const stream = new ReadableStream({
    async start(controller) {
      const reader = upstream.body!.getReader();
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";
          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data:")) continue;
            const payload = trimmed.slice(5).trim();
            if (!payload || payload === "[DONE]") continue;
            let parsed: { choices?: Array<{ delta?: { content?: string } }>; error?: { message?: string } };
            try {
              parsed = JSON.parse(payload) as typeof parsed;
            } catch {
              continue;
            }
            if (parsed.error) {
              controller.enqueue(encoder.encode(`data: ${JSON.stringify({ error: safeProviderMessage(502) })}\n\n`));
              continue;
            }
            const text = parsed.choices?.[0]?.delta?.content ?? "";
            if (text) controller.enqueue(encoder.encode(`data: ${JSON.stringify({ text })}\n\n`));
          }
        }
        controller.enqueue(encoder.encode("data: [DONE]\n\n"));
        controller.close();
      } catch {
        controller.enqueue(encoder.encode(`data: ${JSON.stringify({ error: "The reply stopped before it finished." })}\n\n`));
        controller.close();
      }
    },
  });
  return new Response(stream, {
    headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-store" },
  });
}

export async function speak(text: string, voice: string, speed: number): Promise<Response> {
  const upstream = await postOpenRouter("audio/speech", {
    model: SPEECH_MODEL,
    input: text,
    voice,
    response_format: "mp3",
    speed,
  });
  const type = upstream.headers.get("content-type") ?? "";
  if (!upstream.ok || type.includes("json")) {
    return Response.json({ error: "speech", message: safeProviderMessage(upstream.status), next: "Try again in a moment." }, { status: 502 });
  }
  const bytes = await upstream.arrayBuffer();
  return new Response(bytes, {
    headers: { "Content-Type": "audio/mpeg", "Cache-Control": "no-store" },
  });
}

export async function hear(audio: string, format: string, language: string): Promise<{ text: string } | { error: string }> {
  const upstream = await postOpenRouter("audio/transcriptions", {
    model: HEAR_MODEL,
    input_audio: { data: audio, format },
    language,
  });
  if (!upstream.ok) return { error: safeProviderMessage(upstream.status) };
  let body: { text?: string };
  try {
    body = (await upstream.json()) as { text?: string };
  } catch {
    return { error: safeProviderMessage(502) };
  }
  const text = body.text?.trim() ?? "";
  if (!text) return { error: "No words were heard in that recording." };
  return { text };
}
