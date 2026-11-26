import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import AttemptRunner from "@/components/AttemptRunner";
import ResultsView from "@/components/ResultsView";

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

function subject(name: string, correct: number, supplementary: string | null = null) {
  return { subject: name, correct, total: 25, passed: correct >= 15, supplementary };
}

test("a PPAER partial pass names the subject and its supplementary exam", async () => {
  stubAttempt({
    id: "a1",
    kind: "mock",
    exam: "PPAER",
    correct: 75,
    total: 100,
    pass_percent: 60,
    passed: false,
    outcome: "partial",
    submitted_at: "2026-11-23T13:00:00Z",
    subjects: [
      subject("aeronautics", 25),
      subject("air-law", 25),
      subject("meteorology", 0, "PAMET"),
      subject("navigation", 25),
    ],
    topics: [],
    review: [],
  });
  render(<ResultsView attemptId="a1" />);
  expect(await screen.findByText(/Partial pass/)).toBeDefined();
  expect(screen.getByText(/under 60% in Meteorology/)).toBeDefined();
  expect(screen.getByText(/supplementary exam for each: PAMET/)).toBeDefined();
  const table = screen.getByRole("table", { name: "By subject" });
  expect(table.textContent).toContain("Under 60% (PAMET)");
  expect(table.querySelectorAll("tbody tr")).toHaveLength(4);
});

function reviewed(extra: object) {
  return {
    position: 0,
    question_id: "q1",
    number: null,
    objective_id: "o1",
    topic: "Altimeter setting",
    stem: "What does the altimeter read?",
    choices: ["5 880 ft", "6 120 ft", "6 000 ft", "5 400 ft"],
    origin: "generated",
    chosen_index: 0,
    answer_index: 1,
    correct: false,
    explanation: null,
    source: null,
    references: [],
    ...extra,
  };
}

function resultsWith(item: object) {
  return {
    id: "a1",
    kind: "quiz",
    exam: "PPAER",
    correct: 0,
    total: 1,
    pass_percent: 60,
    passed: false,
    outcome: "fail",
    submitted_at: "2026-11-23T13:00:00Z",
    subjects: [subject("meteorology", 0)],
    topics: [],
    review: [item],
  };
}

test("a reviewed practice question shows why and opens its source", async () => {
  stubAttempt(
    resultsWith(
      reviewed({
        explanation: "TC AIM AIR 1.5.4: 29.92 gives a pressure altitude of 6 120 ft.",
        source: {
          label: "TC AIM AIR 1.5.4",
          chunk_id: "tc-aim:AIR 1.5.4:0",
          document_title: "TC AIM",
          edition: "2026-1",
          jurisdiction: "CA",
          section_ref: "AIR 1.5.4",
          page: 12,
          text: "Setting 29.92 would give a pressure altitude of 6 120 feet.",
        },
      }),
    ),
  );
  render(<ResultsView attemptId="a1" />);
  expect(await screen.findByText(/pressure altitude of 6 120 ft/)).toBeDefined();
  expect(screen.queryByRole("region", { name: /Source detail/ })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Source: TC AIM AIR 1.5.4" }));
  const detail = screen.getByRole("region", { name: "Source detail: TC AIM AIR 1.5.4" });
  expect(detail.textContent).toContain("Setting 29.92 would give");
  expect(detail.textContent).toContain("2026-1");
});

test("a reviewed PSTAR question shows its TP 11919 references", async () => {
  stubAttempt(
    resultsWith(
      reviewed({
        origin: "official",
        number: "9.08",
        references: [
          "CARs 602.77 – Requirement to file an Arrival Report",
          "TC AIM-RAC – Closing a Flight Plan",
        ],
      }),
    ),
  );
  render(<ResultsView attemptId="a1" />);
  expect(await screen.findByText("TP 11919 references:")).toBeDefined();
  expect(screen.getByText("TC AIM-RAC – Closing a Flight Plan")).toBeDefined();
  expect(screen.queryByRole("button", { name: /^Source:/ })).toBeNull();
});

test("a topic's confidence shows the saved rating and sends a change", async () => {
  const topic = {
    objective_id: "o1",
    topic: "Altimeter setting",
    correct: 0,
    total: 1,
    confidence: "medium",
  };
  const fetch = vi.fn();
  fetch
    .mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ ...resultsWith(reviewed({})), topics: [topic] }),
    })
    .mockResolvedValueOnce({ ok: true, status: 204 });
  vi.stubGlobal("fetch", fetch);
  render(<ResultsView attemptId="a1" />);
  const select = (await screen.findByLabelText(
    "Your confidence in Altimeter setting",
  )) as HTMLSelectElement;
  expect(select.value).toBe("medium");
  fireEvent.change(select, { target: { value: "low" } });
  await vi.waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  const [url, init] = fetch.mock.calls[1];
  expect(url).toMatch(/\/objectives\/o1\/confidence$/);
  expect(init.method).toBe("PUT");
  expect(JSON.parse(init.body)).toEqual({ confidence: "low" });
});
