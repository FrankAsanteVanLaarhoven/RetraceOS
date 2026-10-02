/** Conversation jobs and the voices OpenRouter can speak. The key never lives in this file. */

export type JobId = "conversation" | "explain" | "record";
export type Gender = "feminine" | "masculine";
export type Tone = "calm" | "clear" | "bright";
export type Country = "US" | "GB" | "FR";

export type Job = {
  id: JobId;
  label: string;
  model: string;
  purpose: string;
};

export type Voice = {
  id: string;
  name: string;
  gender: Gender;
  country: Country;
  tone: Tone;
  style: string;
};

export const SPEECH_MODEL = "mistralai/voxtral-mini-tts-2603";
export const HEAR_MODEL = "openai/gpt-4o-mini-transcribe";

export const JOBS: Job[] = [
  {
    id: "conversation",
    label: "Conversation",
    model: "anthropic/claude-sonnet-5.5",
    purpose: "The usual conversation. Anthropic Claude Sonnet is the standard model.",
  },
  {
    id: "explain",
    label: "Explain a result",
    model: "anthropic/claude-opus-5.5",
    purpose: "A careful reading of a result. Anthropic Claude Opus does this job. It cannot assign a reproduction result.",
  },
  {
    id: "record",
    label: "Draft a record",
    model: "anthropic/claude-haiku-4.5",
    purpose: "A short record draft. Anthropic Claude Haiku does this job.",
  },
];

/** Voices accepted by mistralai/voxtral-mini-tts-2603. A missing combination is named, not invented. */
export const VOICES: Voice[] = [
  { id: "en_paul_neutral", name: "Paul", gender: "masculine", country: "US", tone: "calm", style: "neutral" },
  { id: "en_paul_confident", name: "Paul", gender: "masculine", country: "US", tone: "clear", style: "confident" },
  { id: "en_paul_cheerful", name: "Paul", gender: "masculine", country: "US", tone: "bright", style: "cheerful" },
  { id: "gb_oliver_neutral", name: "Oliver", gender: "masculine", country: "GB", tone: "calm", style: "neutral" },
  { id: "gb_oliver_confident", name: "Oliver", gender: "masculine", country: "GB", tone: "clear", style: "confident" },
  { id: "gb_oliver_cheerful", name: "Oliver", gender: "masculine", country: "GB", tone: "bright", style: "cheerful" },
  { id: "gb_jane_neutral", name: "Jane", gender: "feminine", country: "GB", tone: "calm", style: "neutral" },
  { id: "gb_jane_confident", name: "Jane", gender: "feminine", country: "GB", tone: "clear", style: "confident" },
  { id: "gb_jane_curious", name: "Jane", gender: "feminine", country: "GB", tone: "bright", style: "curious" },
  { id: "fr_marie_neutral", name: "Marie", gender: "feminine", country: "FR", tone: "calm", style: "neutral" },
  { id: "fr_marie_curious", name: "Marie", gender: "feminine", country: "FR", tone: "clear", style: "curious" },
  { id: "fr_marie_happy", name: "Marie", gender: "feminine", country: "FR", tone: "bright", style: "happy" },
];

const COUNTRY_NAME: Record<Country, string> = {
  US: "United States",
  GB: "United Kingdom",
  FR: "France",
};

export function jobById(id: string): Job | null {
  return JOBS.find((job) => job.id === id) ?? null;
}

export function voiceById(id: string): Voice | null {
  return VOICES.find((voice) => voice.id === id) ?? null;
}

export function resolveVoice(gender: Gender, country: Country, tone: Tone): { voice: Voice; exact: boolean; note: string } {
  const exact = VOICES.find((voice) => voice.gender === gender && voice.country === country && voice.tone === tone);
  if (exact) {
    return { voice: exact, exact: true, note: `${exact.name}, ${COUNTRY_NAME[exact.country]}, ${exact.style}.` };
  }
  const sameCountry = VOICES.find((voice) => voice.country === country && voice.tone === tone) ?? VOICES.find((voice) => voice.country === country);
  const sameGender = VOICES.find((voice) => voice.gender === gender && voice.tone === tone) ?? VOICES.find((voice) => voice.gender === gender);
  const voice = sameCountry ?? sameGender ?? VOICES[0];
  return {
    voice,
    exact: false,
    note: `${voice.name}, ${COUNTRY_NAME[voice.country]}, ${voice.style}. This service has no ${gender} voice for ${COUNTRY_NAME[country]} at that tone, so this is the closest voice.`,
  };
}

export function languageFor(country: Country): "en" | "fr" {
  return country === "FR" ? "fr" : "en";
}

export function speechSpeed(tone: Tone): number {
  if (tone === "calm") return 0.95;
  if (tone === "bright") return 1.05;
  return 1;
}

export function systemPrompt(job: Job): string {
  return [
    "You are the RETRACE conversation assistant on a public platform for scientists.",
    job.purpose,
    "You cannot approve a contract, change a notebook, run an analysis, or assign REPRODUCED_WITHIN_CONTRACT.",
    "A reply is not a reproduction result and it is not a scientific conclusion.",
    "Do not invent measurements. If the scientist did not give a number, say that you do not have it.",
    "Speak in short sentences that a person can hear. Stay under 80 words unless they asked for a record draft.",
    "The record draft, when asked, is a proposal the scientist can edit. It is not stored until they write it on the desk.",
  ].join(" ");
}

export type Turn = { role: "user" | "assistant"; content: string };

export function cleanTurns(input: unknown): Turn[] | null {
  if (!Array.isArray(input) || input.length === 0 || input.length > 8) return null;
  const turns: Turn[] = [];
  for (const item of input) {
    if (!item || typeof item !== "object") return null;
    const role = (item as { role?: unknown }).role;
    const content = (item as { content?: unknown }).content;
    if ((role !== "user" && role !== "assistant") || typeof content !== "string") return null;
    const text = content.trim();
    if (!text || text.length > 2000) return null;
    turns.push({ role, content: text });
  }
  if (turns[turns.length - 1]?.role !== "user") return null;
  return turns;
}
