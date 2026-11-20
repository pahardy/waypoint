import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import Learn from "@/app/learn/page";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

const PHAK = {
  label: "PHAK p.437",
  chunk_id: "faa-phak:437",
  document_title: "Pilot's Handbook of Aeronautical Knowledge",
  edition: "FAA-H-8083-25C",
  jurisdiction: "non-CA",
  section_ref: "PHAK p.437",
  page: 437,
  text: "Alcohol impairs judgment.",
};
const CAR = {
  ...PHAK,
  label: "CAR 602.03",
  chunk_id: "cars:602.03",
  document_title: "Canadian Aviation Regulations",
  edition: "2026-10-01",
  jurisdiction: "CA",
  section_ref: "CAR 602.03",
  page: null,
  text: "Not within 12 hours after drinking.",
};

function respondWith(...events: object[]) {
  const body = events.map((e) => JSON.stringify(e) + "\n").join("");
  const fetch = vi.fn(() => Promise.resolve(new Response(body)));
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

/** The JSON body of the first request made with a stubbed fetch. */
function sentBody(fetch: ReturnType<typeof respondWith>) {
  const [, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
  return JSON.parse(init.body as string);
}

function ask(question: string) {
  fireEvent.change(screen.getByLabelText("Your question"), {
    target: { value: question },
  });
  fireEvent.click(screen.getByRole("button", { name: "Ask" }));
}

test("the page shows the level choice and the disclaimer", () => {
  render(<Learn />);
  expect(screen.getByLabelText("Studying for")).toBeDefined();
  expect(screen.getByText(/educational aid/)).toBeDefined();
});

test("an answer shows citation chips that open the source detail", async () => {
  const fetch = respondWith(
    { type: "delta", text: "Twelve hours [CAR 602.03]. " },
    { type: "delta", text: "Judgment suffers [PHAK p.437]. See [CAR 9.9]." },
    {
      type: "done",
      conversation_id: "c1",
      found: true,
      citations: [CAR, PHAK],
      unknown_references: ["CAR 9.9"],
    },
  );
  render(<Learn />);
  fireEvent.change(screen.getByLabelText("Studying for"), {
    target: { value: "PSTAR" },
  });
  ask("How long after drinking?");

  const chip = await screen.findByRole("button", { name: "Source: CAR 602.03" });
  expect(screen.getByText(/\[CAR 9\.9\]/)).toBeDefined();
  expect(screen.getAllByText("NON-CANADIAN")).toHaveLength(1);

  fireEvent.click(chip);
  expect(chip.getAttribute("aria-expanded")).toBe("true");
  const detail = screen.getByRole("region", { name: "Source detail: CAR 602.03" });
  expect(detail.textContent).toContain("Canadian Aviation Regulations");
  expect(detail.textContent).toContain("2026-10-01");
  expect(detail.textContent).toContain("Not within 12 hours after drinking.");

  const sent = sentBody(fetch);
  expect(sent).toEqual({
    level: "PSTAR",
    messages: [{ role: "user", content: "How long after drinking?" }],
    conversation_id: null,
  });
});

test("a follow-up sends the earlier turns and the conversation id", async () => {
  const done = { type: "done", conversation_id: "c1", found: true, citations: [], unknown_references: [] };
  respondWith({ type: "delta", text: "First." }, done);
  render(<Learn />);
  ask("One?");
  await screen.findByText("First.");

  const fetch = respondWith({ type: "delta", text: "Second." }, done);
  ask("Two?");
  await screen.findByText("Second.");
  const sent = sentBody(fetch);
  expect(sent.messages).toEqual([
    { role: "user", content: "One?" },
    { role: "assistant", content: "First." },
    { role: "user", content: "Two?" },
  ]);
  expect(sent.conversation_id).toBe("c1");
});

test("a model error replaces the partial answer with a clear error", async () => {
  respondWith(
    { type: "delta", text: "Twelve hou" },
    { type: "error", message: "The language model timed out." },
  );
  render(<Learn />);
  ask("How long after drinking?");
  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toContain("The language model timed out.");
  expect(screen.queryByText(/Twelve hou/)).toBeNull();
});

test("a stream that ends without done is reported as incomplete", async () => {
  respondWith({ type: "delta", text: "Twelve hou" });
  render(<Learn />);
  ask("How long after drinking?");
  const alert = await screen.findByRole("alert");
  expect(alert.textContent).toContain("before the answer was complete");
});
