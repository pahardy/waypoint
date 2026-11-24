import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import ExerciseMenu from "@/components/ExerciseMenu";
import ExerciseRunner from "@/components/ExerciseRunner";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
}));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const STAGE_ONE = {
  index: 0,
  id: "before-departure",
  question: "What is the ceiling?",
  answer: "The ceiling is 3,000 ft.",
  marks: [
    {
      criterion_id: "ceiling",
      description: "The student identifies the ceiling.",
      weight: 1,
      mark: "partly_met",
      evidence: "The ceiling is 3,000 ft.",
      reason: "Right ceiling; the scattered layer was not discussed.",
    },
  ],
  score: 50,
};

function session(change: object = {}) {
  return {
    id: "s1",
    exercise_id: "deteriorating-weather",
    kind: "scenario",
    exam: "PPAER",
    intro: "A day VFR cross-country flight.",
    synthetic_notice: "All weather in this scenario is synthetic, for training only.",
    stage_count: 2,
    current: { index: 1, id: "en-route", facts: ["Rain ahead."], question: "What now?" },
    revealed: ["Synthetic METAR: BKN030", "Rain ahead."],
    graded: [STAGE_ONE],
    overall_score: null,
    ...change,
  };
}

function respond(...responses: { status: number; body: object }[]) {
  const fetch = vi.fn();
  for (const { status, body } of responses) {
    fetch.mockResolvedValueOnce({
      ok: status < 400,
      status,
      json: () => Promise.resolve(body),
    });
  }
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

test("a scenario shows the revealed facts, stage feedback and disclaimers", async () => {
  respond({ status: 200, body: session() });
  render(<ExerciseRunner sessionId="s1" />);
  expect(await screen.findByText("Synthetic METAR: BKN030")).toBeDefined();
  expect(screen.getByText("Rain ahead.")).toBeDefined();
  expect(screen.getByText("Educational simulation. Not operational guidance.")).toBeDefined();
  expect(screen.getByText(/synthetic, for training only/)).toBeDefined();

  const feedback = screen.getByRole("region", { name: "Stage 1 feedback" });
  expect(feedback.textContent).toContain("Partly met");
  expect(feedback.textContent).toContain("Right ceiling; the scattered layer");
  expect(feedback.querySelector("blockquote")?.textContent).toBe("The ceiling is 3,000 ft.");
  expect(feedback.textContent).toContain("Score: 50%");

  expect(screen.getByText("Stage 2 of 2")).toBeDefined();
  expect(screen.getByLabelText("What now?")).toBeDefined();
});

test("a finished session shows the overall score and no answer box", async () => {
  respond({ status: 200, body: session({ current: null, overall_score: 75 }) });
  render(<ExerciseRunner sessionId="s1" />);
  expect(await screen.findByText("Overall score: 75%")).toBeDefined();
  expect(screen.queryByRole("textbox")).toBeNull();
});

test("a grading failure keeps the answer so it can be submitted again", async () => {
  respond(
    { status: 200, body: session() },
    { status: 502, body: { detail: "The language model timed out." } },
  );
  render(<ExerciseRunner sessionId="s1" />);
  const box = await screen.findByLabelText("What now?");
  fireEvent.change(box, { target: { value: "Turn back." } });
  fireEvent.click(screen.getByRole("button", { name: "Submit answer" }));
  expect(await screen.findByRole("alert")).toHaveProperty(
    "textContent",
    "The language model timed out.",
  );
  expect((box as HTMLTextAreaElement).value).toBe("Turn back.");
});

test("each exercise is listed under its own name", async () => {
  respond({
    status: 200,
    body: [
      { id: "fuel-reserve", kind: "scenario", exam: "PPAER", prompt: "A flight." },
      { id: "radio-failure", kind: "scenario", exam: "PPAER", prompt: "A flight." },
    ],
  });
  render(<ExerciseMenu />);
  expect(await screen.findByRole("heading", { name: "Fuel reserve" })).toBeDefined();
  expect(screen.getByRole("heading", { name: "Radio failure" })).toBeDefined();
  expect(screen.getAllByText("Scenario, PPAER")).toHaveLength(2);
});
