import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true, // Enable React strict mode
  output: "standalone", // Enable standalone output for optimized Docker builds
};

export default nextConfig;
