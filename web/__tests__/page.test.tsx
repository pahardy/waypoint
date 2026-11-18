import { afterEach, expect, test, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import Home from "@/app/page";
import ApiStatus from "@/components/ApiStatus";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function stubFetch(result: Promise<unknown>) {
  vi.stubGlobal("fetch", vi.fn(() => result));
}

test("home page renders the title and disclaimer", () => {
  stubFetch(new Promise(() => {}));
  render(<Home />);
  expect(screen.getByRole("heading", { level: 1, name: "Waypoint" })).toBeDefined();
  expect(screen.getByText(/educational aid/)).toBeDefined();
});

test("API status shows connected when health is ok", async () => {
  stubFetch(Promise.resolve({ json: () => Promise.resolve({ status: "ok" }) }));
  render(<ApiStatus />);
  expect(await screen.findByText("API: connected")).toBeDefined();
});

test("API status shows unreachable when the request fails", async () => {
  stubFetch(Promise.reject(new Error("offline")));
  render(<ApiStatus />);
  expect(await screen.findByText("API: unreachable")).toBeDefined();
});
