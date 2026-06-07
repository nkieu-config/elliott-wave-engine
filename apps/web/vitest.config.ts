import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";

// Library + component/hook unit tests. Default node env; DOM-dependent tests opt
// in per-file with `// @vitest-environment jsdom`.
export default defineConfig({
  test: {
    environment: "node",
    include: ["lib/**/*.test.{ts,tsx}", "components/**/*.test.{ts,tsx}"],
    alias: { "@": fileURLToPath(new URL(".", import.meta.url)) },
  },
});
