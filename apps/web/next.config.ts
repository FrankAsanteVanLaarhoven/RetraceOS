import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  distDir: process.env.RETRACE_NEXT_DIST || ".next",
  poweredByHeader: false,
  reactStrictMode: true,
  productionBrowserSourceMaps: false,
  devIndicators: false,
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(self), geolocation=()" },
        ],
      },
    ];
  },
};

export default nextConfig;
