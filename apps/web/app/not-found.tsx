import Link from "next/link";

export default function NotFound() {
  return (
    <main className="main" id="content">
      <p className="eyebrow">404</p>
      <h1>That page is not on this desk.</h1>
      <p>The address does not match a RETRACE view.</p>
      <p>
        <Link className="primary" href="/">
          Return to the desk
        </Link>
      </p>
    </main>
  );
}
