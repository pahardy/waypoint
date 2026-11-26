import { afterEach, expect, test, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import FlightTestChecklist from "@/components/FlightTestChecklist";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function item(change: object = {}) {
  return {
    objective_id: "flight-test.ex22a",
    exercise: "Ex. 22 Forced Landing",
    title: "Control/Approach",
    aim: "To plan, manage and safely carry out a successful approach.",
    reference: "TP 13723 Ex. 22 A",
    source: null,
    exercise_ids: ["forced-landing"],
    reviewed: false,
    note: "",
    ...change,
  };
}

function respond(items: object[]) {
  const fetch = vi.fn();
  fetch
    .mockResolvedValueOnce({ ok: true, status: 200, json: () => Promise.resolve(items) })
    .mockResolvedValue({ ok: true, status: 204 });
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

test("a row shows its status as text, and the count", async () => {
  respond([
    item(),
    item({
      objective_id: "flight-test.ex22b",
      title: "Cockpit Management",
      exercise_ids: [],
      reviewed: true,
    }),
  ]);
  render(<FlightTestChecklist />);
  expect(await screen.findByText("1 of 2 items marked reviewed")).toBeDefined();
  expect(screen.getByText("TO REVIEW")).toBeDefined();
  expect(screen.getByText("REVIEWED")).toBeDefined();
  expect(screen.getByRole("link", { name: "Forced landing" }).getAttribute("href")).toBe(
    "/exercises",
  );
});

test("the checkbox saves the mark and updates the count", async () => {
  const fetch = respond([item()]);
  render(<FlightTestChecklist />);
  fireEvent.click(await screen.findByLabelText("Reviewed"));
  expect(await screen.findByText("1 of 1 items marked reviewed")).toBeDefined();
  const [url, init] = fetch.mock.calls[1];
  expect(url).toMatch(/\/flight-test\/flight-test\.ex22a$/);
  expect(JSON.parse(init.body)).toEqual({ reviewed: true, note: "" });
});

test("the note saves on blur", async () => {
  const fetch = respond([item()]);
  render(<FlightTestChecklist />);
  const note = await screen.findByLabelText("Questions for my instructor");
  fireEvent.change(note, { target: { value: "Which fields near the airport?" } });
  expect(fetch).toHaveBeenCalledTimes(1);
  fireEvent.blur(note);
  await vi.waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
  expect(JSON.parse(fetch.mock.calls[1][1].body)).toEqual({
    reviewed: false,
    note: "Which fields near the airport?",
  });
});
