import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  // Enable rewrites to proxy API requests to the backend (solves Mixed Content issues)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://187.127.142.58/api/:path*',
      },
    ];
  },
};

export default nextConfig;
