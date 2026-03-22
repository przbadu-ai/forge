import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  compress: false,  // Required: prevents Next.js from buffering SSE responses
};

export default nextConfig;
