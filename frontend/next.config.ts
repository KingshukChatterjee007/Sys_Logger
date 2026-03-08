import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  // Enable rewrites to proxy API requests to the backend (solves Mixed Content issues)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5010'}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
