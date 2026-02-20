import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'standalone',
<<<<<<< HEAD
  // Enable rewrites to proxy API requests to the backend (solves Mixed Content issues)
=======
  // Proxy API and Socket.IO to backend to avoid Mixed Content (HTTPS -> HTTP)
>>>>>>> 94571205259c2bf6c077a807c402a192098f910c
  async rewrites() {
    return [
      {
        source: '/api/:path*',
<<<<<<< HEAD
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'}/api/:path*`,
=======
        destination: 'http://127.0.0.1:5010/api/:path*',
      },
      {
        source: '/socket.io/',
        destination: 'http://127.0.0.1:5010/socket.io/',
      },
      {
        source: '/socket.io/:path*',
        destination: 'http://127.0.0.1:5010/socket.io/:path*',
>>>>>>> 94571205259c2bf6c077a807c402a192098f910c
      },
    ];
  },
};

export default nextConfig;
