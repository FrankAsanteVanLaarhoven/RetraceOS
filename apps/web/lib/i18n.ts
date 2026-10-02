import en from "./messages/en.json";

const cache: Record<string, Record<string, string>> = { en };

const loaders: Record<string, () => Promise<{ default: Record<string, string> }>> = {
  nl: () => import("./messages/nl.json"),
  fr: () => import("./messages/fr.json"),
  de: () => import("./messages/de.json"),
  es: () => import("./messages/es.json"),
  it: () => import("./messages/it.json"),
  pt: () => import("./messages/pt.json"),
  sv: () => import("./messages/sv.json"),
  da: () => import("./messages/da.json"),
  nb: () => import("./messages/nb.json"),
  fi: () => import("./messages/fi.json"),
  pl: () => import("./messages/pl.json"),
  cs: () => import("./messages/cs.json"),
  sk: () => import("./messages/sk.json"),
  ro: () => import("./messages/ro.json"),
  hu: () => import("./messages/hu.json"),
  el: () => import("./messages/el.json"),
  tr: () => import("./messages/tr.json"),
  uk: () => import("./messages/uk.json"),
  ru: () => import("./messages/ru.json"),
  ar: () => import("./messages/ar.json"),
  he: () => import("./messages/he.json"),
  fa: () => import("./messages/fa.json"),
  hi: () => import("./messages/hi.json"),
  bn: () => import("./messages/bn.json"),
  ur: () => import("./messages/ur.json"),
  ta: () => import("./messages/ta.json"),
  te: () => import("./messages/te.json"),
  "zh-Hans": () => import("./messages/zh-Hans.json"),
  ja: () => import("./messages/ja.json"),
  ko: () => import("./messages/ko.json"),
  vi: () => import("./messages/vi.json"),
  th: () => import("./messages/th.json"),
  id: () => import("./messages/id.json"),
  sw: () => import("./messages/sw.json"),
  ak: () => import("./messages/ak.json"),
};

export const RTL = new Set(["ar", "he", "fa", "ur"]);

export async function loadLocale(locale: string): Promise<void> {
  if (cache[locale]) return;
  const load = loaders[locale];
  if (!load) return;
  try {
    const mod = await load();
    cache[locale] = mod.default ?? (mod as unknown as Record<string, string>);
  } catch {
    cache[locale] = cache.en;
  }
}

export function translate(locale: string, key: string, vars?: Record<string, string>): string {
  const table = cache[locale] ?? cache.en;
  let text = table[key] ?? cache.en[key] ?? key;
  if (vars) text = text.replace(/\{(\w+)\}/g, (_, name: string) => vars[name] ?? "");
  return text;
}
