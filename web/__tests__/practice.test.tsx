import { afterEach, expect, test, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import AttemptRunner from "@/components/AttemptRunner";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function attemptWith(origin: "official" | "generated", number: string | null) {
  return {
    id: "a1",
    kind: "quiz",
    exam: origin === "official" ? "PSTAR" : "PPAER",
    started_at: "2026-11-23T12:00:00Z",
    deadline: null,
    submitted_at: null,
    questions: [
      {
        position: 0,
        question_id: "q1",
        number,
        objective_id: "o1",
        topic: "Minimum Altitude and Distances",
        stem: "Over a built-up area, the minimum altitude is",
        choices: ["500 ft", "1,000 ft", "1,500 ft", "2,000 ft"],
        origin,
        chosen_index: null,
      },
    ],
  };
}

function stubAttempt(attempt: object) {
  vi.stubGlobal(
    "fetch",
    vi.fn(() => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(attempt) })),
  );
}

test("a generated question is labelled as a practice question", async () => {
  stubAttempt(attemptWith("generated", null));
  render(<AttemptRunner attemptId="a1" />);
  expect(await screen.findByText("PRACTICE")).toBeDefined();
  expect(screen.queryByText("OFFICIAL")).toBeNull();
  expect(screen.queryByText(/TP 11919/)).toBeNull();
});

test("an official question is labelled official with its TP 11919 number", async () => {
  stubAttempt(attemptWith("official", "1.07"));
  render(<AttemptRunner attemptId="a1" />);
  expect(await screen.findByText("OFFICIAL")).toBeDefined();
  expect(screen.getByText("TP 11919 1.07")).toBeDefined();
  expect(screen.queryByText("PRACTICE")).toBeNull();
});
