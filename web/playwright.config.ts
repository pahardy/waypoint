import { defineConfig, devices } from "@playwright/test";

/** End-to-end tests: the built site against the API with a stub model.
 * The API needs a migrated database in DATABASE_URL. */
export default defineConfig({
  testDir: "e2e",
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? "github" : "list",
  use: { baseURL: "http://localhost:3000" },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "phone", use: { ...devices["Pixel 7"] } },
  ],
  webServer: [
    {
      command: "uv run python tests/stub_server.py",
      cwd: "../api",
      url: "http://localhost:8000/health",
      reuseExistingServer: !process.env.CI,
    },
    {
      command: "npm run build && npm run start",
      url: "http://localhost:3000",
      reuseExistingServer: !process.env.CI,
      timeout: 180_000,
    },
  ],
});
