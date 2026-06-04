import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  poweredByHeader: false,
  allowedDevOrigins: ["without-specialists-incentives-sales.trycloudflare.com"],
  serverExternalPackages: ["kysely"],
};

export default nextConfig;
