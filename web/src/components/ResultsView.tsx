"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Badge from "@/components/Badge";
import { type Results, getResults } from "@/lib/practice";

function percent(correct: number, total: number): number {
  return Math.round((correct * 100) / total);
}

/** A submitted attempt: score, topic breakdown and question review. */
export default function ResultsView({ attemptId }: { attemptId: string }) {
  const [results, setResults] = useState<Results | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getResults(attemptId)
      .then(setResults)
      .catch(() => setError("These results could not be loaded."));
  }, [attemptId]);

  if (error) return <p role="alert" className="text-fail">{error}</p>;
  if (!results) return <p role="status">Loading...</p>;

  const title = results.kind === "mock" ? "Mock exam" : "Quiz";
  return (
    <div className="flex flex-col gap-8">
      <section aria-labelledby="score-heading" className="flex flex-col gap-2 rounded bg-surface p-5">
        <h2 id="score-heading" className="font-display text-2xl font-bold uppercase">
          {title} score
        </h2>
        <p className="text-3xl font-semibold">
          {results.correct} / {results.total} ({percent(results.correct, results.total)}%)
        </p>
        <p className={results.passed ? "text-pass" : "text-fail"}>
          {results.passed ? "At or above" : "Below"} the {results.pass_percent}%{" "}
          {results.exam} pass mark.
        </p>
        <p className="text-sm text-muted">
          A practice result only. It does not predict your result on the
          Transport Canada examination.
        </p>
      </section>

      <section aria-labelledby="topics-heading" className="flex flex-col gap-3">
        <h2 id="topics-heading" className="font-display text-2xl font-bold uppercase">
          By topic
        </h2>
        <table className="w-full text-left">
          <thead className="text-sm text-muted">
            <tr>
              <th scope="col" className="py-1">Topic</th>
              <th scope="col" className="py-1 text-right">Correct</th>
            </tr>
          </thead>
          <tbody>
            {results.topics.map((t) => (
              <tr key={t.objective_id} className="border-t border-surface">
                <td className="py-2">{t.topic}</td>
                <td className="py-2 text-right font-mono">
                  {t.correct} / {t.total}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section aria-labelledby="review-heading" className="flex flex-col gap-4">
        <h2 id="review-heading" className="font-display text-2xl font-bold uppercase">
          Question review
        </h2>
        <ol className="flex flex-col gap-4">
          {results.review.map((item) => (
            <li key={item.position} className="flex flex-col gap-2 rounded bg-surface p-5">
              <p className="flex flex-wrap items-center gap-2 text-sm text-muted">
                <span className={item.correct ? "text-pass" : "text-fail"}>
                  {item.correct ? "Correct" : "Incorrect"}
                </span>
                <Badge variant={item.origin === "official" ? "official" : "practice"} />
                {item.number && <span>TP 11919 {item.number}</span>}
              </p>
              <p className="whitespace-pre-line">{item.stem}</p>
              <p>
                <span className="text-muted">Your answer: </span>
                {item.chosen_index === null ? "Not answered" : item.choices[item.chosen_index]}
              </p>
              {!item.correct && (
                <p>
                  <span className="text-muted">Correct answer: </span>
                  {item.choices[item.answer_index]}
                </p>
              )}
            </li>
          ))}
        </ol>
      </section>

      <Link href="/practice" className="text-sky underline">
        Practise again
      </Link>
    </div>
  );
}
