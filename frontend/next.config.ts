import { spawnSync } from "node:child_process";
import withSerwistInit from "@serwist/next";
import type { NextConfig } from "next";

const revision =
  spawnSync("git", ["rev-parse", "HEAD"], { encoding: "utf-8" }).stdout?.trim() ??
  crypto.randomUUID();

const withSerwist = withSerwistInit({
  swSrc: "src/app/sw.ts",
  swDest: "public/sw.js",
  additionalPrecacheEntries: [{ url: "/~offline", revision }],
});

const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  compress: false, // Required: prevents Next.js from buffering SSE responses
  turbopack: {}, // Silence Turbopack warning; Serwist uses webpack plugin for SW generation
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/sw.js",
        headers: [
          {
            key: "Content-Type",
            value: "application/javascript; charset=utf-8",
          },
          {
            key: "Cache-Control",
            value: "no-cache, no-store, must-revalidate",
          },
          {
            key: "Service-Worker-Allowed",
            value: "/",
          },
        ],
      },
    ];
  },
};

export default withSerwist(nextConfig);
