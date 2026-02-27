// ✅ CORRECT (ES Module)
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    optimizePackageImports: ['@xenova/transformers'],
    webpack: config => {
      config.experiments = { ...config.experiments, topLevelAwait: true };
      return config;
    }
  },
  transpilePackages: ['@xenova/transformers']
};

export default nextConfig;