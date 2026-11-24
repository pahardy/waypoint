"use client";

import { useEffect, useState } from "react";
import {
  type GradedStage,
  MARK_LABELS,
  SIMULATION,
  type Session,
  answerStage,
  getSession,
} from "@/lib/exercises";

/** One graded stage: the question, the student's answer, each criterion's
 * mark with its evidence and reason, and the stage score. */
function StageFeedback({ stage, count }: { stage: GradedStage; count: number }) {
  const title = count > 1 ? `Stage ${stage.index + 1} feedback` : "Feedback";
  return (
    <section aria-label={title} className="flex flex-col gap-3 rounded bg-surface p-5">
      <h2 className="font-display text-2xl font-bold uppercase">{title}</h2>
      <p className="font-semibold">{stage.question}</p>
      <p className="whitespace-pre-wrap text-muted">{stage.answer}</p>
      <ul className="flex flex-col gap-3">
        {stage.marks.map((m) => (
          <li key={m.criterion_id}>
            <p>
              <span className="font-semibold">{MARK_LABELS[m.mark]}</span>: {m.description}{" "}
              <span className="text-muted">(weight {m.weight})</span>
            </p>
            {m.evidence && <blockquote className="border-l-2 border-muted pl-3">{m.evidence}</blockquote>}
            <p className="text-muted">{m.reason}</p>
          </li>
        ))}
      </ul>
      <p className="font-semibold">Score: {stage.score}%</p>
    </section>
  );
}

/** An oral exercise or scenario in progress: the facts so far, the current
 * question and the feedback on every answered stage. Reloading continues the
 * session where it was left. */
export default function ExerciseRunner({ sessionId }: { sessionId: string }) {
  const [session, setSession] = useState<Session | null>(null);
  const [answer, setAnswer] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [grading, setGrading] = useState(false);

  useEffect(() => {
    getSession(sessionId)
      .then(setSession)
      .catch(() => setError("This exercise could not be loaded."));
  }, [sessionId]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setGrading(true);
    setError(null);
    try {
      setSession(await answerStage(sessionId, answer.trim()));
      setAnswer("");
    } catch (e) {
      setError((e as Error).message);
    }
    setGrading(false);
  }

  if (!session) {
    return error ? <p role="alert" className="text-fail">{error}</p> : <p role="status">Loading...</p>;
  }

  const current = session.current;
  return (
    <div className="flex flex-col gap-6">
      <p className="font-semibold">{SIMULATION}</p>
      {session.synthetic_notice && <p className="text-accent">{session.synthetic_notice}</p>}
      {session.intro && <p>{session.intro}</p>}
      {session.revealed.length > 0 && (
        <section aria-label="What you know so far" className="flex flex-col gap-2">
          <h2 className="font-display text-xl font-bold uppercase">What you know so far</h2>
          <ul className="list-disc pl-5 font-mono text-sm">
            {session.revealed.map((fact) => (
              <li key={fact}>{fact}</li>
            ))}
          </ul>
        </section>
      )}
      {session.graded.map((stage) => (
        <StageFeedback key={stage.index} stage={stage} count={session.stage_count} />
      ))}
      {current ? (
        <form onSubmit={submit} className="flex flex-col gap-3">
          {session.stage_count > 1 && (
            <p className="text-muted">
              Stage {current.index + 1} of {session.stage_count}
            </p>
          )}
          <label htmlFor="answer" className="font-semibold">
            {current.question}
          </label>
          <textarea
            id="answer"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={6}
            className="rounded border border-muted bg-surface p-3"
          />
          {error && <p role="alert" className="text-fail">{error}</p>}
          <button
            type="submit"
            disabled={grading || !answer.trim()}
            className="self-start rounded bg-accent px-4 py-2 font-semibold text-on-accent disabled:opacity-50"
          >
            {grading ? "Grading..." : "Submit answer"}
          </button>
        </form>
      ) : (
        <p className="text-2xl font-semibold">Overall score: {session.overall_score}%</p>
      )}
    </div>
  );
}
