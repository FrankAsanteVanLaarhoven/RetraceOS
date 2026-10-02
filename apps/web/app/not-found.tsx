import Link from "next/link";
import { Copy, ViewTitle } from "@/components/Copy";

export default function NotFound() {
  return (
    <main className="main" id="content">
      <ViewTitle k="missing.title" />
      <Copy as="p" className="eyebrow" k="missing.eyebrow" />
      <Copy as="h1" k="missing.title" />
      <Copy as="p" k="missing.body" />
      <p>
        <Link className="primary" href="/">
          <Copy k="missing.home" />
        </Link>
      </p>
    </main>
  );
}
