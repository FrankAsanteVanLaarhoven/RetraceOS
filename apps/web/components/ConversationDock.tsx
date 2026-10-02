"use client";

import { useEffect, useId, useRef, useState } from "react";
import { useDesk } from "@/components/DeskProvider";
import { Notice } from "@/components/Status";
import {
  HEAR_MODEL,
  JOBS,
  SPEECH_MODEL,
  jobById,
  languageFor,
  resolveVoice,
  type Country,
  type Gender,
  type JobId,
  type Tone,
  type Turn,
} from "@/lib/assistant";

type Phase = "idle" | "listening" | "hearing" | "thinking" | "speaking";
type Problem = { message: string; next?: string };

const COUNTRIES: Country[] = ["US", "GB", "FR"];
const GENDERS: Gender[] = ["feminine", "masculine"];
const TONES: Tone[] = ["calm", "clear", "bright"];

async function readError(response: Response, fallback: Problem): Promise<Problem> {
  const body = (await response.json().catch(() => null)) as Problem | null;
  return body?.message ? body : fallback;
}

function bytesToBase64(bytes: Uint8Array): string {
  let binary = "";
  for (let index = 0; index < bytes.length; index += 0x4000) {
    binary += String.fromCharCode(...bytes.subarray(index, index + 0x4000));
  }
  return btoa(binary);
}

export function ConversationDock() {
  const { t } = useDesk();
  const titleId = useId();
  const opener = useRef<HTMLButtonElement>(null);
  const field = useRef<HTMLTextAreaElement>(null);
  const turnsRef = useRef<Turn[]>([]);
  const liveRef = useRef(false);
  const generation = useRef(0);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const stopRecord = useRef<(() => void) | null>(null);
  const choiceRef = useRef({ job: "conversation" as JobId, gender: "masculine" as Gender, country: "US" as Country, tone: "calm" as Tone, speak: true });
  const [open, setOpen] = useState(false);
  const [configured, setConfigured] = useState<boolean | null>(null);
  const [job, setJob] = useState<JobId>("conversation");
  const [gender, setGender] = useState<Gender>("masculine");
  const [country, setCountry] = useState<Country>("US");
  const [tone, setTone] = useState<Tone>("calm");
  const [speakReplies, setSpeakReplies] = useState(true);
  const [draft, setDraft] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [phase, setPhase] = useState<Phase>("idle");
  const [live, setLive] = useState(false);
  const [error, setError] = useState<Problem | null>(null);
  const busy = phase !== "idle";
  choiceRef.current = { job, gender, country, tone, speak: speakReplies };

  useEffect(() => {
    let gone = false;
    fetch("/api/assistant")
      .then((response) => response.json())
      .then((body: { configured?: boolean }) => {
        if (!gone) setConfigured(Boolean(body.configured));
      })
      .catch(() => {
        if (!gone) setConfigured(false);
      });
    return () => {
      gone = true;
    };
  }, []);

  function remember(next: Turn[]) {
    const kept = next.slice(-8);
    turnsRef.current = kept;
    setTurns(kept);
  }

  function stopAudio() {
    audioRef.current?.pause();
    audioRef.current = null;
  }

  function stopAll() {
    generation.current += 1;
    liveRef.current = false;
    setLive(false);
    stopRecord.current?.();
    stopRecord.current = null;
    stopAudio();
    setPhase("idle");
  }

  function openPanel() {
    setOpen(true);
    requestAnimationFrame(() => field.current?.focus({ preventScroll: true }));
  }

  function closePanel() {
    stopAll();
    setOpen(false);
    requestAnimationFrame(() => opener.current?.focus());
  }

  async function playMp3(blob: Blob): Promise<void> {
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audioRef.current = audio;
    await new Promise<void>((resolve, reject) => {
      let started = false;
      const finish = () => {
        URL.revokeObjectURL(url);
        if (audioRef.current === audio) audioRef.current = null;
        resolve();
      };
      audio.onplaying = () => {
        started = true;
      };
      audio.onended = finish;
      audio.onpause = () => {
        if (started || audioRef.current !== audio) finish();
      };
      audio.onerror = () => {
        URL.revokeObjectURL(url);
        reject(new Error("playback"));
      };
      void audio.play().catch(() => {
        URL.revokeObjectURL(url);
        reject(new Error("playback"));
      });
    });
  }

  async function converse(text: string, aloud: boolean) {
    const token = generation.current;
    const prior = turnsRef.current.slice(-7);
    const messages = [...prior, { role: "user" as const, content: text }];
    remember(messages);
    setDraft("");
    setPhase("thinking");
    setError(null);
    const response = await fetch("/api/assistant", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job: choiceRef.current.job, messages }),
    });
    if (generation.current !== token) return;
    if (!response.ok || !response.body) {
      setError(await readError(response, { message: t("talk.replyError"), next: t("talk.replyNext") }));
      setPhase("idle");
      return;
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let full = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";
      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith("data:")) continue;
        const payload = line.slice(5).trim();
        if (!payload || payload === "[DONE]") continue;
        const parsed = JSON.parse(payload) as { text?: string; error?: string };
        if (parsed.error) {
          setError({ message: parsed.error, next: t("talk.replyNext") });
          setPhase("idle");
          return;
        }
        if (parsed.text) {
          full += parsed.text;
          remember([...messages, { role: "assistant", content: full }]);
        }
      }
    }
    if (generation.current !== token) return;
    if (!full.trim()) {
      setError({ message: t("talk.replyError"), next: t("talk.replyNext") });
      setPhase("idle");
      return;
    }
    if (aloud && choiceRef.current.speak) {
      setPhase("speaking");
      const spoken = await fetch("/api/assistant/speech", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: full.slice(0, 700),
          voice: resolveVoice(choiceRef.current.gender, choiceRef.current.country, choiceRef.current.tone).voice.id,
          tone: choiceRef.current.tone,
        }),
      });
      if (generation.current !== token) return;
      if (!spoken.ok) {
        setError(await readError(spoken, { message: t("talk.speechError"), next: t("talk.replyNext") }));
        setPhase("idle");
        return;
      }
      try {
        await playMp3(await spoken.blob());
      } catch {
        if (generation.current === token) setError({ message: t("talk.playback"), next: t("talk.playbackNext") });
      }
    }
    if (generation.current === token) setPhase("idle");
  }

  function recordTurn(): Promise<{ blob: Blob | null; denied: boolean }> {
    return new Promise((resolve) => {
      let settled = false;
      const finish = (blob: Blob | null, denied = false) => {
        if (settled) return;
        settled = true;
        stopRecord.current = null;
        resolve({ blob, denied });
      };
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((stream) => {
          try {
            const context = new AudioContext();
            const source = context.createMediaStreamSource(stream);
            const analyser = context.createAnalyser();
            analyser.fftSize = 2048;
            source.connect(analyser);
            const samples = new Uint8Array(analyser.fftSize);
            const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus") ? "audio/webm;codecs=opus" : "audio/webm";
            const recorder = new MediaRecorder(stream, { mimeType: mime });
            const chunks: Blob[] = [];
            recorder.ondataavailable = (event) => {
              if (event.data.size) chunks.push(event.data);
            };
            const started = Date.now();
            let heard = false;
            let silentSince: number | null = null;
            let cancelled = false;
            const release = () => {
              stream.getTracks().forEach((track) => track.stop());
              void context.close();
            };
            const halt = () => {
              cancelled = true;
              window.clearInterval(timer);
              recorder.onstop = () => {
                release();
                finish(null);
              };
              if (recorder.state === "inactive") {
                release();
                finish(null);
              } else recorder.stop();
            };
            stopRecord.current = halt;
            const timer = window.setInterval(() => {
              analyser.getByteTimeDomainData(samples);
              let sum = 0;
              for (const value of samples) {
                const sample = (value - 128) / 128;
                sum += sample * sample;
              }
              const rms = Math.sqrt(sum / samples.length);
              if (rms > 0.02) {
                heard = true;
                silentSince = null;
              } else if (heard) {
                silentSince ??= Date.now();
              }
              const quiet = heard && silentSince !== null && Date.now() - silentSince > 800;
              const tooLong = Date.now() - started > 18000;
              const unheard = !heard && Date.now() - started > 8000;
              if (!quiet && !tooLong && !unheard) return;
              window.clearInterval(timer);
              recorder.onstop = () => {
                release();
                finish(cancelled || !heard ? null : new Blob(chunks, { type: "audio/webm" }));
              };
              if (recorder.state === "inactive") finish(null);
              else recorder.stop();
            }, 100);
            recorder.start();
          } catch {
            stream.getTracks().forEach((track) => track.stop());
            finish(null, true);
          }
        })
        .catch(() => finish(null, true));
    });
  }

  async function listenOnce() {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setError({ message: t("talk.noRecorder"), next: t("talk.micNext") });
      liveRef.current = false;
      setLive(false);
      return;
    }
    setError(null);
    setPhase("listening");
    const recording = await recordTurn();
    if (!liveRef.current) {
      setPhase("idle");
      return;
    }
    if (recording.denied) {
      setError({ message: t("talk.micDenied"), next: t("talk.micNext") });
      liveRef.current = false;
      setLive(false);
      setPhase("idle");
      return;
    }
    const blob = recording.blob;
    if (!blob) {
      setError({ message: t("talk.silent"), next: t("talk.micNext") });
      liveRef.current = false;
      setLive(false);
      setPhase("idle");
      return;
    }
    if (blob.size > 1_400_000) {
      setError({ message: t("talk.tooLong"), next: t("talk.micNext") });
      liveRef.current = false;
      setLive(false);
      setPhase("idle");
      return;
    }
    setPhase("hearing");
    const audio = bytesToBase64(new Uint8Array(await blob.arrayBuffer()));
    const heard = await fetch("/api/assistant/hear", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ audio, format: "webm", language: languageFor(choiceRef.current.country) }),
    });
    if (!heard.ok) {
      setError(await readError(heard, { message: t("talk.hearError"), next: t("talk.micNext") }));
      liveRef.current = false;
      setLive(false);
      setPhase("idle");
      return;
    }
    const body = (await heard.json()) as { text?: string };
    const text = body.text?.trim() ?? "";
    if (!text) {
      setError({ message: t("talk.silent"), next: t("talk.micNext") });
      liveRef.current = false;
      setLive(false);
      setPhase("idle");
      return;
    }
    await converse(text.slice(0, 2000), true);
    if (liveRef.current) void listenOnce();
  }

  async function sendDraft() {
    const text = draft.trim();
    if (!text || busy || configured === false) return;
    try {
      await converse(text.slice(0, 2000), speakReplies);
    } catch {
      setError({ message: t("talk.replyError"), next: t("talk.replyNext") });
      setPhase("idle");
    }
  }

  function toggleLive() {
    if (liveRef.current) {
      stopAll();
      return;
    }
    liveRef.current = true;
    setLive(true);
    void listenOnce().catch(() => {
      setError({ message: t("talk.hearError"), next: t("talk.micNext") });
      liveRef.current = false;
      setLive(false);
      setPhase("idle");
    });
  }

  const selected = jobById(job) ?? JOBS[0];
  const resolved = resolveVoice(gender, country, tone);
  const voiceFields = {
    name: resolved.voice.name,
    country: t(`talk.country.${resolved.voice.country}`),
    tone: t(`talk.tone.${tone}`),
    style: t(`talk.style.${resolved.voice.style}`),
  };
  const voiceNote = resolved.exact
    ? t("talk.voiceExact", voiceFields)
    : t("talk.voiceClosest", {
        ...voiceFields,
        gender: t(`talk.gender.${gender}`),
        asked: t(`talk.country.${country}`),
      });
  const phaseLabel =
    phase === "listening"
      ? t("talk.listening")
      : phase === "hearing"
        ? t("talk.hearing")
        : phase === "thinking"
          ? t("talk.thinking")
          : phase === "speaking"
            ? t("talk.speaking")
            : t("talk.notStored");

  if (!open) {
    return (
      <button ref={opener} className="talk-launcher primary" type="button" onClick={openPanel}>
        {t("talk.open")}
      </button>
    );
  }

  return (
    <section
      className="talk-panel"
      role="dialog"
      aria-labelledby={titleId}
      onKeyDown={(event) => {
        if (event.key === "Escape") closePanel();
      }}
    >
      <div className="talk-head">
        <h2 id={titleId}>{t("talk.title")}</h2>
        <button className="ghost" type="button" onClick={closePanel}>
          {t("talk.close")}
        </button>
      </div>
      <p>{t("talk.lede")}</p>
      <p className="talk-models">
        {t("talk.standard")}: {selected.model}. {t("talk.speechModel")}: {SPEECH_MODEL}. {t("talk.hearModel")}: {HEAR_MODEL}.
      </p>
      {configured === null ? <p role="status">{t("talk.checking")}</p> : null}
      {configured === false ? <Notice message={t("talk.needs")} next={t("talk.needsNext")} /> : null}
      <div className="talk-choices">
        <div className="field">
          <label htmlFor="talk-job">{t("talk.job")}</label>
          <select id="talk-job" value={job} onChange={(event) => setJob(event.target.value as JobId)}>
            {JOBS.map((item) => (
              <option key={item.id} value={item.id}>
                {t(`talk.job.${item.id}`)}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="talk-country">{t("talk.country")}</label>
          <select id="talk-country" value={country} onChange={(event) => setCountry(event.target.value as Country)}>
            {COUNTRIES.map((item) => (
              <option key={item} value={item}>
                {t(`talk.country.${item}`)}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="talk-gender">{t("talk.gender")}</label>
          <select id="talk-gender" value={gender} onChange={(event) => setGender(event.target.value as Gender)}>
            {GENDERS.map((item) => (
              <option key={item} value={item}>
                {t(`talk.gender.${item}`)}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="talk-tone">{t("talk.tone")}</label>
          <select id="talk-tone" value={tone} onChange={(event) => setTone(event.target.value as Tone)}>
            {TONES.map((item) => (
              <option key={item} value={item}>
                {t(`talk.tone.${item}`)}
              </option>
            ))}
          </select>
        </div>
      </div>
      <p id="talk-voice" data-exact={resolved.exact ? "yes" : "no"}>
        {voiceNote}
      </p>
      <ol className="talk-log" aria-live="polite">
        {turns.map((turn, index) => (
          <li key={`${turn.role}-${index}`} data-role={turn.role}>
            <span>{turn.role === "user" ? t("talk.you") : t("talk.assistant")}</span>
            {turn.content}
          </li>
        ))}
      </ol>
      <p role="status">{phaseLabel}</p>
      {error ? <Notice message={error.message} next={error.next} /> : null}
      <div className="field">
        <label htmlFor="talk-message">{t("talk.message")}</label>
        <textarea
          ref={field}
          id="talk-message"
          rows={3}
          value={draft}
          maxLength={2000}
          placeholder={t("talk.placeholder")}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void sendDraft();
            }
          }}
        />
      </div>
      <label className="check">
        <input type="checkbox" checked={speakReplies} onChange={(event) => setSpeakReplies(event.target.checked)} />
        {t("talk.speak")}
      </label>
      <div className="talk-actions">
        <button className="primary" type="button" disabled={busy || configured !== true || !draft.trim()} aria-busy={phase === "thinking"} onClick={() => void sendDraft()}>
          {phase === "thinking" ? t("talk.sending") : t("talk.send")}
        </button>
        <button className="ghost" type="button" aria-pressed={live} disabled={configured !== true || (busy && !live)} onClick={toggleLive}>
          {live ? t("talk.liveOn") : t("talk.live")}
        </button>
        <button className="ghost" type="button" disabled={!busy && !live} onClick={stopAll}>
          {t("talk.stop")}
        </button>
      </div>
    </section>
  );
}
