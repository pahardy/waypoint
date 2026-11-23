"use client";

import { useId, useState } from "react";
import Badge from "@/components/Badge";
import CitationChip from "@/components/CitationChip";
import SourceDetail from "@/components/SourceDetail";
import {
  type Citation,
  LEVELS,
  type Level,
  type Turn,
  postChat,
  readEvents,
  segments,
} from "@/lib/chat";

type Exchange = {
  question: string;
  answer: string;
  citations: Citation[];
  status: "streaming" | "done" | "error";
  error?: string;
};

const INCOMPLETE = "The connection ended before the answer was complete.";

/** The completed turns, oldest first, for the next request. */
function history(exchanges: Exchange[]): Turn[] {
  return exchanges
    .filter((e) => e.status === "done")
    .flatMap((e) => [
      { role: "user" as const, content: e.question },
      { role: "assistant" as const, content: e.answer },
    ]);
}

/** The instructor chat: pick a level, ask, and read the answer as it streams. */
export default function Chat() {
  const [level, setLevel] = useState<Level>("PPAER");
  const [draft, setDraft] = useState("");
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const busy = exchanges.at(-1)?.status === "streaming";

  function update(change: Partial<Exchange> | ((e: Exchange) => Partial<Exchange>)) {
    setExchanges((all) => {
      const last = all.at(-1)!;
      const patch = typeof change === "function" ? change(last) : change;
      return [...all.slice(0, -1), { ...last, ...patch }];
    });
  }

  async function ask(event: React.FormEvent) {
    event.preventDefault();
    const question = draft.trim();
    if (!question || busy) return;
    const messages = [...history(exchanges), { role: "user" as const, content: question }];
    setDraft("");
    setExchanges((all) => [
      ...all,
      { question, answer: "", citations: [], status: "streaming" },
    ]);
    try {
      const body = await postChat(level, messages, conversationId);
      for await (const event of readEvents(body)) {
        if (event.type === "delta") {
          update((e) => ({ answer: e.answer + event.text }));
        } else if (event.type === "done") {
          setConversationId(event.conversation_id);
          update({ citations: event.citations, status: "done" });
          return;
        } else {
          update({ status: "error", error: event.message });
          return;
        }
      }
      update({ status: "error", error: INCOMPLETE });
    } catch (error) {
      update({ status: "error", error: (error as Error).message });
    }
  }

  function restart() {
    setExchanges([]);
    setConversationId(null);
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center gap-3">
        <label htmlFor="level" className="font-medium">
          Studying for
        </label>
        <select
          id="level"
          value={level}
          onChange={(e) => setLevel(e.target.value as Level)}
          className="min-h-11 rounded border border-muted bg-surface px-3"
        >
          {Object.entries(LEVELS).map(([value, name]) => (
            <option key={value} value={value}>
              {name}
            </option>
          ))}
        </select>
        {exchanges.length > 0 && (
          <button
            type="button"
            onClick={restart}
            disabled={busy}
            className="min-h-11 rounded px-3 text-sky underline disabled:opacity-50"
          >
            New conversation
          </button>
        )}
      </div>

      <div role="log" aria-label="Conversation" className="flex flex-col gap-6">
        {exchanges.map((exchange, i) => (
          <ExchangeView key={i} exchange={exchange} />
        ))}
      </div>

      <form onSubmit={ask} className="flex flex-col gap-2 sm:flex-row">
        <label htmlFor="question" className="sr-only">
          Your question
        </label>
        <textarea
          id="question"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) ask(e);
          }}
          rows={2}
          maxLength={8000}
          placeholder="Ask about air law, navigation, weather or aircraft..."
          className="flex-1 rounded border border-muted bg-surface p-3"
        />
        <button
          type="submit"
          disabled={busy || !draft.trim()}
          className="min-h-11 rounded bg-accent px-5 font-semibold text-on-accent disabled:opacity-50"
        >
          Ask
        </button>
      </form>
    </div>
  );
}

function ExchangeView({ exchange }: { exchange: Exchange }) {
  const detailId = useId();
  const [open, setOpen] = useState<Citation | null>(null);
  const toggle = (c: Citation) => setOpen(open?.chunk_id === c.chunk_id ? null : c);

  return (
    <article className="flex flex-col gap-3">
      <p className="self-end rounded bg-surface px-4 py-2">
        <span className="sr-only">You asked: </span>
        {exchange.question}
      </p>
      <div className="border-l-2 border-sky pl-4" aria-busy={exchange.status === "streaming"}>
        <h2 className="sr-only">Instructor answer</h2>
        {exchange.status === "error" ? (
          <p role="alert" className="text-fail">
            Error: the answer could not be completed. {exchange.error} Please try
            again.
          </p>
        ) : (
          <p className="whitespace-pre-wrap">
            {exchange.status === "streaming"
              ? exchange.answer || "Thinking..."
              : segments(exchange.answer, exchange.citations).map((s, i) =>
                  s.kind === "text" ? (
                    s.text
                  ) : (
                    <CitationChip
                      key={i}
                      citation={s.citation}
                      open={open?.chunk_id === s.citation.chunk_id}
                      detailId={detailId}
                      onToggle={() => toggle(s.citation)}
                    />
                  ),
                )}
          </p>
        )}
        {exchange.status === "done" && exchange.citations.length > 0 && (
          <Sources citations={exchange.citations} />
        )}
        <div id={detailId}>{open && <SourceDetail citation={open} />}</div>
      </div>
    </article>
  );
}

function Sources({ citations }: { citations: Citation[] }) {
  return (
    <ul className="mt-3 flex flex-col gap-1 text-sm text-muted">
      {citations.map((c) => (
        <li key={c.chunk_id}>
          <span className="font-mono">{c.label}</span>: {c.document_title}, {c.edition}{" "}
          {c.jurisdiction === "non-CA" && <Badge variant="non-CA" />}
        </li>
      ))}
    </ul>
  );
}
