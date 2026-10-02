import { Copy, ViewTitle } from "@/components/Copy";

export default function Loading() {
  return (
    <main className="main" id="content" aria-busy="true">
      <ViewTitle k="loading.title" />
      <Copy as="p" className="eyebrow" k="loading.eyebrow" />
      <Copy as="h1" k="loading.title" />
      <Copy as="p" k="loading.body" />
    </main>
  );
}
