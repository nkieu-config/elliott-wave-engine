import { withSentryConfig } from "@sentry/nextjs";

// CSP left permissive-by-omission (app loads no third-party scripts);
// frame/MIME/referrer/HSTS are the cheap wins.
const SECURITY_HEADERS = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Content-Security-Policy", value: "frame-ancestors 'none'" },
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
];

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Emit a self-contained server (.next/standalone) so the Docker runtime image
  // ships only traced deps — no full node_modules. See apps/web/Dockerfile.
  output: "standalone",
  async headers() {
    return [{ source: "/:path*", headers: SECURITY_HEADERS }];
  },
  // Tree-shake barrel exports; explicit list is version-proof. lucide-react
  // alone ships ~1000 icons via a barrel index.
  experimental: {
    optimizePackageImports: [
      "lucide-react",
      "@radix-ui/react-dialog",
      "@radix-ui/react-label",
      "@radix-ui/react-select",
      "@radix-ui/react-slider",
      "@radix-ui/react-slot",
      "@radix-ui/react-tooltip",
    ],
  },
  webpack: (config) => {
    // Silence @opentelemetry/instrumentation's `Critical dependency`
    // expression-require warnings (dynamic require() webpack can't analyze; no
    // runtime impact). Narrow regex so OTHER such warnings still surface.
    config.ignoreWarnings = [
      ...(config.ignoreWarnings ?? []),
      {
        module: /node_modules\/@opentelemetry\/instrumentation/,
        message: /Critical dependency: the request of a dependency is an expression/,
      },
    ];
    return config;
  },
};

// Source-map upload only with a CI/prod auth token — keeps the DSN-less local
// build untouched (no Sentry webpack plugin, no chunks added).
export default process.env.SENTRY_AUTH_TOKEN
  ? withSentryConfig(nextConfig, {
      org: process.env.SENTRY_ORG,
      project: process.env.SENTRY_PROJECT,
      authToken: process.env.SENTRY_AUTH_TOKEN,
      silent: true,
      widenClientFileUpload: true,
      tunnelRoute: "/monitoring",
    })
  : nextConfig;
