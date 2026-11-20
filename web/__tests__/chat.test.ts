import { expect, test } from "vitest";
import { type Citation, readEvents, segments } from "@/lib/chat";

const CAR: Citation = {
  label: "CAR 602.03",
  chunk_id: "cars:CAR 602.03:0",
  document_title: "Canadian Aviation Regulations",
  edition: "2026-10-01",
  jurisdiction: "CA",
  section_ref: "CAR 602.03",
  page: null,
  text: "Not within 12 hours.",
};
const AIM: Citation = { ...CAR, label: "TC AIM AIR 3.9", chunk_id: "aim" };

function streamOf(...chunks: string[]): ReadableStream<BufferSource> {
  const encoder = new TextEncoder();
  return new ReadableStream({
    start(controller) {
      chunks.forEach((c) => controller.enqueue(encoder.encode(c)));
      controller.close();
    },
  });
}

test("events are parsed from lines split across chunks", async () => {
  const body = streamOf('{"type":"delta","te', 'xt":"Hi"}\n{"type":"error",', '"message":"x"}\n');
  const events = [];
  for await (const event of readEvents(body)) events.push(event);
  expect(events).toEqual([
    { type: "delta", text: "Hi" },
    { type: "error", message: "x" },
  ]);
});

test("cited labels become citations and the text around them is kept", () => {
  expect(segments("Twelve hours [CAR 602.03]. Done.", [CAR])).toEqual([
    { kind: "text", text: "Twelve hours " },
    { kind: "cite", citation: CAR },
    { kind: "text", text: ". Done." },
  ]);
});

test("several labels in one bracket become several citations", () => {
  expect(segments("[TC AIM AIR 3.9; CAR 602.03]", [CAR, AIM])).toEqual([
    { kind: "cite", citation: AIM },
    { kind: "cite", citation: CAR },
  ]);
});

test("a reference with no citation stays plain text", () => {
  expect(segments("See [CAR 999.99].", [CAR])).toEqual([
    { kind: "text", text: "See " },
    { kind: "text", text: "[CAR 999.99]" },
    { kind: "text", text: "." },
  ]);
});
