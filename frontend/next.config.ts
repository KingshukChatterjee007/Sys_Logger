import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
  // Proxy API and Socket.IO to backend to avoid Mixed Content (HTTPS -> HTTP)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:5010/api/:path*',
      },
      {
        source: '/socket.io',
        destination: 'http://127.0.0.1:5010/socket.io/',
      },
      {
        source: '/socket.io/:path+',
        destination: 'http://127.0.0.1:5010/socket.io/:path*',
      },
    ];
  },
};

export default nextConfig;
