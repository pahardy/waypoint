import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import ProgressView from "@/components/ProgressView";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  push.mockReset();
});

function respond(...bodies: object[]) {
  const fetch = vi.fn();
  for (const body of bodies) {
    fetch.mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve(body) });
  }
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

const OCCURRENCES = {
  objective_id: "pstar.regulations.014",
  topic: "Aviation Occurrences",
  correct: 2,
  seen: 5,
  percent: 40,
  reason: "2 of 5 correct (40%), below the 90% pass mark",
};

function progress(change: object = {}) {
  return {
    exam: "PSTAR",
    pass_percent: 90,
    subjects: [{ subject: "regulations", correct: 2, seen: 5, percent: 40 }],
    weak: [OCCURRENCES],
    recommendations: [OCCURRENCES],
    ...change,
  };
}

test("subjects show their numbers", async () => {
  respond(progress());
  render(<ProgressView />);
  const row = (await screen.findByRole("table", { name: "By subject" })).querySelector("tbody tr");
  expect(row?.textContent).toBe("Aviation Regulations2540%");
});

test("a recommendation shows its reason and starts a topic quiz", async () => {
  const fetch = respond(progress(), { id: "a1" });
  render(<ProgressView />);
  const card = await screen.findByRole("region", { name: "Aviation Occurrences" });
  expect(within(card).getByText(OCCURRENCES.reason)).toBeDefined();
  fireEvent.click(within(card).getByRole("button", { name: "Start quiz" }));
  await vi.waitFor(() => expect(push).toHaveBeenCalledWith("/practice/a1"));
  expect(JSON.parse(fetch.mock.calls[1][1].body)).toEqual({
    exam: "PSTAR",
    kind: "quiz",
    objective_id: "pstar.regulations.014",
  });
});

test("the full weak list is collapsed with its count", async () => {
  respond(progress());
  render(<ProgressView />);
  const summary = await screen.findByText("All weak objectives (1)");
  expect(summary.closest("details")?.open).toBe(false);
});

test("nothing weak points to a mixed quiz", async () => {
  respond(
    progress({
      subjects: [{ subject: "regulations", correct: 5, seen: 5, percent: 100 }],
      weak: [],
      recommendations: [],
    }),
  );
  render(<ProgressView />);
  expect(await screen.findByText(/No weak objectives at the moment/)).toBeDefined();
  expect(screen.getByRole("link", { name: "Practice" }).getAttribute("href")).toBe("/practice");
  expect(screen.queryByText(/All weak objectives/)).toBeNull();
});

test("an exam with no answers shows the empty state", async () => {
  respond(
    progress({
      subjects: [{ subject: "regulations", correct: 0, seen: 0, percent: null }],
      weak: [],
      recommendations: [],
    }),
  );
  render(<ProgressView />);
  expect(await screen.findByText(/No PSTAR questions answered yet/)).toBeDefined();
  expect(screen.queryByRole("table")).toBeNull();
});
