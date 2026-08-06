import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    let backendUrl = process.env.BACKEND_URL || "http://localhost:8010";
    backendUrl = backendUrl
      .replace(/^http:\/([^/])/, "http://$1")
      .replace(/^https:\/([^/])/, "https://$1");
    if (backendUrl.endsWith("/")) {
      backendUrl = backendUrl.slice(0, -1);
    }
    return [{ source: "/api/:path*", destination: `${backendUrl}/api/:path*` }];
  },
};

export default nextConfig;
