/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Enable standalone output for Docker deployment
  output: process.env.DOCKER_BUILD ? "standalone" : undefined,
};
module.exports = nextConfig;
