import { afterEach, expect, test, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import ProgressView from "@/components/ProgressView";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function respond(body: object) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok: true, status: 200, json: () => Promise.resolve(body) }),
  );
}

test("subjects and weak objectives show their numbers", async () => {
  respond({
    exam: "PSTAR",
    pass_percent: 90,
    subjects: [{ subject: "regulations", correct: 2, seen: 5, percent: 40 }],
    weak: [
      {
        objective_id: "pstar.regulations.014",
        topic: "Aviation Occurrences",
        correct: 2,
        seen: 5,
        percent: 40,
        reason: "2 of 5 correct (40%), below the 90% pass mark",
      },
    ],
  });
  render(<ProgressView />);
  const row = (await screen.findByRole("table", { name: "By subject" })).querySelector("tbody tr");
  expect(row?.textContent).toBe("Aviation Regulations2540%");
  expect(screen.getByText("Aviation Occurrences")).toBeDefined();
  expect(screen.getByText("2 of 5 correct (40%), below the 90% pass mark")).toBeDefined();
});

test("an exam with no answers shows the empty state", async () => {
  respond({
    exam: "PSTAR",
    pass_percent: 90,
    subjects: [{ subject: "regulations", correct: 0, seen: 0, percent: null }],
    weak: [],
  });
  render(<ProgressView />);
  expect(await screen.findByText(/No PSTAR questions answered yet/)).toBeDefined();
  expect(screen.queryByRole("table")).toBeNull();
});

test("no weak objectives says so", async () => {
  respond({
    exam: "PSTAR",
    pass_percent: 90,
    subjects: [{ subject: "regulations", correct: 5, seen: 5, percent: 100 }],
    weak: [],
  });
  render(<ProgressView />);
  expect(await screen.findByText("None at the moment.")).toBeDefined();
});
