import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

// Separate from vitest.config.ts (node, lib-only): this one renders real
// components under jsdom to profile re-render counts.
export default defineConfig({
  resolve: {
    alias: { "@": fileURLToPath(new URL(".", import.meta.url)) },
  },
  // rolldown-vite uses oxc; force the automatic JSX runtime so the root
  // tsconfig's `jsx: preserve` (needed by Next) doesn't break the transform.
  oxc: { jsx: { runtime: "automatic" } },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["profile/**/*.test.tsx"],
  },
});
