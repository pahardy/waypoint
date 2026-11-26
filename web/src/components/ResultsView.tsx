"use client";

import Link from "next/link";
import { useEffect, useId, useState } from "react";
import Badge from "@/components/Badge";
import CitationChip from "@/components/CitationChip";
import SourceDetail from "@/components/SourceDetail";
import {
  type Confidence,
  type ReviewItem,
  SUBJECTS,
  type Results,
  type SubjectScore,
  type TopicScore,
  getResults,
  rateConfidence,
} from "@/lib/practice";

function percent(correct: number, total: number): number {
  return Math.round((correct * 100) / total);
}

/** What the outcome means, in the exam's own terms (TP 12880 for PPAER). */
function OutcomeText({ results }: { results: Results }) {
  const mark = `${results.pass_percent}% ${results.exam} pass mark`;
  if (results.outcome === "pass") {
    return <p className="text-pass">Pass: at or above the {mark}.</p>;
  }
  if (results.outcome === "fail") {
    return <p className="text-fail">Fail: below the {mark}.</p>;
  }
  const failed = results.subjects.filter((s) => !s.passed);
  return (
    <p className="text-fail">
      Partial pass: {results.pass_percent}% or more overall, but under{" "}
      {results.pass_percent}% in {failed.map((s) => SUBJECTS[s.subject] ?? s.subject).join(", ")}.
      On the Transport Canada exam this means a supplementary exam for each:{" "}
      {failed.map((s) => s.supplementary).join(", ")}.
    </p>
  );
}

function SubjectRow({ score, passPercent }: { score: SubjectScore; passPercent: number }) {
  return (
    <tr className="border-t border-surface">
      <td className="py-2">{SUBJECTS[score.subject] ?? score.subject}</td>
      <td className="py-2 text-right font-mono">
        {score.correct} / {score.total} ({percent(score.correct, score.total)}%)
      </td>
      <td className={`py-2 text-right ${score.passed ? "text-pass" : "text-fail"}`}>
        {score.passed ? `${passPercent}% or more` : `Under ${passPercent}%`}
        {score.supplementary && ` (${score.supplementary})`}
      </td>
    </tr>
  );
}

/** One answered question: the answers, why the correct one is right, and
 * its source (a cited passage, or the references TP 11919 gives). */
function ReviewCard({ item }: { item: ReviewItem }) {
  const [open, setOpen] = useState(false);
  const detailId = useId();
  return (
    <li className="flex flex-col gap-2 rounded bg-surface p-5">
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
      {item.explanation && (
        <p>
          <span className="text-muted">Why: </span>
          {item.explanation}
        </p>
      )}
      {item.source && (
        <div>
          <span className="text-muted">Source: </span>
          <CitationChip
            citation={item.source}
            open={open}
            detailId={detailId}
            onToggle={() => setOpen(!open)}
          />
          <div id={detailId}>{open && <SourceDetail citation={item.source} />}</div>
        </div>
      )}
      {item.references.length > 0 && (
        <div>
          <p className="text-muted">TP 11919 references:</p>
          <ul className="list-disc pl-5 text-sm">
            {item.references.map((ref) => (
              <li key={ref}>{ref}</li>
            ))}
          </ul>
        </div>
      )}
    </li>
  );
}

/** A submitted attempt: score, subject and topic breakdown, question review. */
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
        <OutcomeText results={results} />
        <p className="text-sm text-muted">
          A practice result only. It does not predict your result on the
          Transport Canada examination.
        </p>
      </section>

      {results.subjects.length > 1 && (
        <section aria-labelledby="subjects-heading" className="flex flex-col gap-3">
          <h2 id="subjects-heading" className="font-display text-2xl font-bold uppercase">
            By subject
          </h2>
          <table aria-labelledby="subjects-heading" className="w-full text-left">
            <thead className="text-sm text-muted">
              <tr>
                <th scope="col" className="py-1">Subject</th>
                <th scope="col" className="py-1 text-right">Correct</th>
                <th scope="col" className="py-1 text-right">Result</th>
              </tr>
            </thead>
            <tbody>
              {results.subjects.map((s) => (
                <SubjectRow key={s.subject} score={s} passPercent={results.pass_percent} />
              ))}
            </tbody>
          </table>
        </section>
      )}

      <section aria-labelledby="topics-heading" className="flex flex-col gap-3">
        <h2 id="topics-heading" className="font-display text-2xl font-bold uppercase">
          By topic
        </h2>
        <table aria-labelledby="topics-heading" className="w-full text-left">
          <thead className="text-sm text-muted">
            <tr>
              <th scope="col" className="py-1">Topic</th>
              <th scope="col" className="py-1 text-right">Correct</th>
              <th scope="col" className="py-1 text-right">Your confidence</th>
            </tr>
          </thead>
          <tbody>
            {results.topics.map((t) => (
              <tr key={t.objective_id} className="border-t border-surface">
                <td className="py-2">{t.topic}</td>
                <td className="py-2 text-right font-mono">
                  {t.correct} / {t.total}
                </td>
                <td className="py-2 text-right">
                  <ConfidenceSelect topic={t} />
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
            <ReviewCard key={item.position} item={item} />
          ))}
        </ol>
      </section>

      <Link href="/practice" className="text-sky underline">
        Practise again
      </Link>
    </div>
  );
}

const CONFIDENCE_LABELS: Record<Confidence, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
};

/** The student's confidence in a topic, saved as soon as it changes. */
function ConfidenceSelect({ topic }: { topic: TopicScore }) {
  const [value, setValue] = useState<string>(topic.confidence ?? "");
  const [error, setError] = useState(false);

  async function change(next: string) {
    setValue(next);
    try {
      await rateConfidence(topic.objective_id, (next || null) as Confidence | null);
      setError(false);
    } catch {
      setError(true);
    }
  }

  return (
    <>
      <select
        aria-label={`Your confidence in ${topic.topic}`}
        value={value}
        onChange={(e) => change(e.target.value)}
        className="rounded border border-muted bg-bg p-1"
      >
        <option value="">Not rated</option>
        {Object.entries(CONFIDENCE_LABELS).map(([key, label]) => (
          <option key={key} value={key}>
            {label}
          </option>
        ))}
      </select>
      {error && (
        <p role="alert" className="text-sm text-fail">
          Not saved.
        </p>
      )}
    </>
  );
}
