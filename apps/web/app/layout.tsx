import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Desk", template: "%s · RETRACE" },
  description:
    "Local workstation for recovering a computational analysis, reviewing every change, and checking it against a researcher-approved contract.",
  applicationName: "RETRACE",
  robots: { index: false, follow: false },
};

const themeBoot = `(function(){try{var t=localStorage.getItem("retrace-theme")||"system";var d=localStorage.getItem("retrace-density")||"comfortable";var root=document.documentElement;root.dataset.density=d;root.dataset.themeChoice=t;var resolved=t==="system"?(window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"):t;root.dataset.theme=resolved;var dir=localStorage.getItem("retrace-dir");if(dir==="rtl"||dir==="ltr")root.dir=dir;}catch(e){}})();`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" data-theme="light" data-density="comfortable" suppressHydrationWarning>
      <body>
        <script dangerouslySetInnerHTML={{ __html: themeBoot }} />
        {children}
      </body>
    </html>
  );
}
