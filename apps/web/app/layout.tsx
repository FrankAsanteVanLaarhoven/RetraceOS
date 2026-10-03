import type { Metadata } from "next";
import type { ReactNode } from "react";
import { ConversationDock } from "@/components/ConversationDock";
import { DeskProvider } from "@/components/DeskProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: { default: "Desk", template: "%s · RETRACE" },
  description:
    "Public platform for scientists. Keep the original notebook, approve what a result must mean, and check a rerun against that approval.",
  applicationName: "RETRACE",
  robots: { index: false, follow: false },
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "16x16 32x32 48x48" },
      { url: "/icon.svg", type: "image/svg+xml" },
    ],
    apple: [{ url: "/apple-icon.png", sizes: "180x180", type: "image/png" }],
  },
};

const themeBoot = `(function(){try{var t=localStorage.getItem("retrace-theme")||"system";var d=localStorage.getItem("retrace-density")||"comfortable";var root=document.documentElement;root.dataset.density=d;root.dataset.themeChoice=t;var resolved=t==="system"?(window.matchMedia("(prefers-color-scheme: dark)").matches?"dark":"light"):t;root.dataset.theme=resolved;var loc=localStorage.getItem("retrace-locale")||"en";root.lang=loc;var rtl={ar:1,he:1,fa:1,ur:1};var dir=localStorage.getItem("retrace-dir");if(dir!=="rtl"&&dir!=="ltr")dir=rtl[loc]?"rtl":"ltr";root.dir=dir;}catch(e){}})();`;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" data-theme="light" data-density="comfortable" suppressHydrationWarning>
      <body>
        <script dangerouslySetInnerHTML={{ __html: themeBoot }} />
        <div className="scene" aria-hidden="true">
          <div className="scene-world">
            <div className="scene-west" />
            <div className="scene-east" />
          </div>
        </div>
        <DeskProvider>
          {children}
          <ConversationDock />
        </DeskProvider>
      </body>
    </html>
  );
}
