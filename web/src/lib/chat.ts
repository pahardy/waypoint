/** Talking to the instructor: POST /chat streams JSON Lines events. */

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const LEVELS = {
  PSTAR: "PSTAR (Student Pilot Permit)",
  PPAER: "PPAER (PPL written exam)",
  FLIGHT_TEST: "PPL flight test",
} as const;

export type Level = keyof typeof LEVELS;

export type Turn = { role: "user" | "assistant"; content: string };

export type Citation = {
  label: string;
  chunk_id: string;
  document_title: string;
  edition: string;
  jurisdiction: "CA" | "non-CA";
  section_ref: string;
  page: number | null;
  text: string;
};

export type ChatEvent =
  | { type: "delta"; text: string }
  | {
      type: "done";
      conversation_id: string;
      found: boolean;
      citations: Citation[];
      unknown_references: string[];
    }
  | { type: "error"; message: string };

/** Send the conversation and return the response body to read events from. */
export async function postChat(
  level: Level,
  messages: Turn[],
  conversationId: string | null,
): Promise<ReadableStream<BufferSource>> {
  const response = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ level, messages, conversation_id: conversationId }),
  });
  if (!response.ok || !response.body) {
    throw new Error(`The instructor could not be reached (${response.status}).`);
  }
  return response.body;
}

/** Parse a JSON Lines stream into events, one per line. */
export async function* readEvents(
  body: ReadableStream<BufferSource>,
): AsyncGenerator<ChatEvent> {
  const lines = body
    .pipeThrough(new TextDecoderStream())
    .pipeThrough(splitLines());
  for await (const line of lines) {
    if (line.trim()) yield JSON.parse(line) as ChatEvent;
  }
}

function splitLines(): TransformStream<string, string> {
  let buffer = "";
  return new TransformStream({
    transform(chunk, controller) {
      buffer += chunk;
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";
      lines.forEach((line) => controller.enqueue(line));
    },
    flush(controller) {
      controller.enqueue(buffer);
    },
  });
}

export type Segment =
  | { kind: "text"; text: string }
  | { kind: "cite"; citation: Citation };

/** Split an answer into text and citations. A bracketed reference that
 * matches no citation stays as plain text, so it never looks verified. */
export function segments(text: string, citations: Citation[]): Segment[] {
  const byLabel = new Map(citations.map((c) => [c.label, c]));
  const result: Segment[] = [];
  let last = 0;
  for (const match of text.matchAll(/\[([^[\]]+)\]/g)) {
    result.push({ kind: "text", text: text.slice(last, match.index) });
    for (const reference of match[1].split(";").map((r) => r.trim())) {
      const citation = byLabel.get(reference);
      result.push(
        citation ? { kind: "cite", citation } : { kind: "text", text: `[${reference}]` },
      );
    }
    last = match.index + match[0].length;
  }
  result.push({ kind: "text", text: text.slice(last) });
  return result.filter((s) => s.kind === "cite" || s.text);
}
