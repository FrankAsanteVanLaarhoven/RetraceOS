import type { Metadata } from "next";
import { Offline } from "@/components/Offline";
import { api } from "@/lib/server";

export const metadata: Metadata = { title: "Privacy" };

type Notice = {
  audience: string;
  cookie: { name: string; purpose: string; duration: string; flags: string; tracking: string };
  stored: string[];
  not_done: string[];
  rights: { export: string; erasure: string; sign_out: string };
  cache: string;
  hashing: string;
  rate_limit: string;
  separation: string;
  controller: string;
  assessment: string;
};

export default async function PrivacyPage() {
  const response = await api("/api/privacy");
  if (!response?.ok) return <Offline />;
  const notice = (await response.json()) as Notice;
  return (
    <main className="main" id="content">
      <article className="guide">
        <p className="eyebrow">Public platform</p>
        <h1>Privacy and your record</h1>
        <p>{notice.audience}</p>
        <h2>Session cookie</h2>
        <ul>
          <li>Name: {notice.cookie.name}</li>
          <li>{notice.cookie.purpose}</li>
          <li>Duration: {notice.cookie.duration}</li>
          <li>{notice.cookie.flags}</li>
          <li>{notice.cookie.tracking}</li>
        </ul>
        <h2>What this service stores</h2>
        <ul>
          {notice.stored.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <h2>What this service does not do</h2>
        <ul>
          {notice.not_done.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <h2>Your record</h2>
        <ul>
          <li>{notice.rights.export}</li>
          <li>{notice.rights.erasure}</li>
          <li>{notice.rights.sign_out}</li>
        </ul>
        <p>{notice.cache}</p>
        <p>{notice.hashing}</p>
        <p>{notice.rate_limit}</p>
        <p>{notice.separation}</p>
        <p>{notice.controller}</p>
        <p>{notice.assessment}</p>
        <p>
          <a className="text-link" href="/login">
            Sign in
          </a>
        </p>
      </article>
    </main>
  );
}
