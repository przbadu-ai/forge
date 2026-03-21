import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  compress: false,  // Required: prevents Next.js from buffering SSE responses
};

export default nextConfig;
