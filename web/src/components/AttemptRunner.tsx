"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import Badge from "@/components/Badge";
import Timer from "@/components/Timer";
import {
  ApiError,
  type Attempt,
  type AttemptQuestion,
  answer,
  getAttempt,
  submit,
} from "@/lib/practice";

/** A quiz or mock exam in progress. Choices are saved as they are made. */
export default function AttemptRunner({ attemptId }: { attemptId: string }) {
  const router = useRouter();
  const [attempt, setAttempt] = useState<Attempt | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const finish = useCallback(async () => {
    setSubmitting(true);
    try {
      await submit(attemptId);
      router.push(`/results/${attemptId}`);
    } catch (e) {
      setError((e as Error).message);
      setSubmitting(false);
    }
  }, [attemptId, router]);

  useEffect(() => {
    getAttempt(attemptId)
      .then((loaded) => {
        if (loaded.submitted_at) router.replace(`/results/${attemptId}`);
        else setAttempt(loaded);
      })
      .catch(() => setError("This attempt could not be loaded."));
  }, [attemptId, router]);

  async function choose(question: AttemptQuestion, chosenIndex: number) {
    const previous = question.chosen_index;
    setChosen(question.position, chosenIndex);
    try {
      await answer(attemptId, question.position, chosenIndex);
    } catch (e) {
      setChosen(question.position, previous);
      if (e instanceof ApiError && e.status === 409) await finish();
      else setError((e as Error).message);
    }
  }

  function setChosen(position: number, chosenIndex: number | null) {
    setAttempt((a) =>
      a && {
        ...a,
        questions: a.questions.map((q) =>
          q.position === position ? { ...q, chosen_index: chosenIndex } : q,
        ),
      },
    );
  }

  if (error && !attempt) return <p role="alert" className="text-fail">{error}</p>;
  if (!attempt) return <p role="status">Loading...</p>;

  const total = attempt.questions.length;
  const answered = attempt.questions.filter((q) => q.chosen_index !== null).length;
  return (
    <div className="flex flex-col gap-6">
      <div className="sticky top-0 z-10 flex items-center justify-between gap-4 border-b border-surface bg-bg py-3">
        <p>
          {answered} of {total} answered
        </p>
        {attempt.deadline && <Timer deadline={attempt.deadline} onExpire={finish} />}
      </div>
      {error && <p role="alert" className="text-fail">{error}</p>}
      <ol className="flex flex-col gap-6">
        {attempt.questions.map((q) => (
          <li key={q.position}>
            <QuestionCard
              question={q}
              total={total}
              disabled={submitting}
              onChoose={(index) => choose(q, index)}
            />
          </li>
        ))}
      </ol>
      <button
        type="button"
        disabled={submitting}
        onClick={finish}
        className="self-start rounded bg-accent px-4 py-2 font-semibold text-on-accent disabled:opacity-50"
      >
        Submit answers
      </button>
    </div>
  );
}

function QuestionCard({
  question,
  total,
  disabled,
  onChoose,
}: {
  question: AttemptQuestion;
  total: number;
  disabled: boolean;
  onChoose: (index: number) => void;
}) {
  const label = `Question ${question.position + 1} of ${total}`;
  return (
    <fieldset className="flex flex-col gap-3 rounded bg-surface p-5" disabled={disabled}>
      <legend className="sr-only">{label}</legend>
      <p className="flex flex-wrap items-center gap-2 text-sm text-muted">
        <span>{label}</span>
        <Badge variant={question.origin === "official" ? "official" : "practice"} />
        {question.number && <span>TP 11919 {question.number}</span>}
        <span>{question.topic}</span>
      </p>
      <p className="whitespace-pre-line">{question.stem}</p>
      {question.choices.map((choice, index) => (
        <label key={index} className="flex items-start gap-3">
          <input
            type="radio"
            name={`question-${question.position}`}
            checked={question.chosen_index === index}
            onChange={() => onChoose(index)}
            className="mt-1.5"
          />
          <span>{choice}</span>
        </label>
      ))}
    </fieldset>
  );
}
