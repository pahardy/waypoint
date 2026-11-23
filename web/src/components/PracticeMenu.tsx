"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Badge from "@/components/Badge";
import { type ExamInfo, type Kind, getExam, startAttempt } from "@/lib/practice";

const ALL_TOPICS = "";

/** Choose a PSTAR topic quiz or the timed mock exam. */
export default function PracticeMenu() {
  const router = useRouter();
  const [info, setInfo] = useState<ExamInfo | null>(null);
  const [topic, setTopic] = useState(ALL_TOPICS);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    getExam("PSTAR")
      .then(setInfo)
      .catch(() => setError("The practice questions could not be loaded."));
  }, []);

  async function start(kind: Kind) {
    setStarting(true);
    try {
      const attempt = await startAttempt("PSTAR", kind, topic || null);
      router.push(`/practice/${attempt.id}`);
    } catch (e) {
      setError((e as Error).message);
      setStarting(false);
    }
  }

  if (error) return <p role="alert" className="text-fail">{error}</p>;
  if (!info) return <p role="status">Loading...</p>;

  const minutes = info.time_limit_s / 60;
  const timeUnverified = info.unverified.includes("time_limit_s");
  return (
    <div className="flex flex-col gap-8">
      <section aria-labelledby="quiz-heading" className="flex flex-col gap-3 rounded bg-surface p-5">
        <h2 id="quiz-heading" className="font-display text-2xl font-bold uppercase">
          Topic quiz
        </h2>
        <p className="text-muted">
          {info.quiz_length} questions, untimed. Choose one TP 11919 section or
          mix them all.
        </p>
        <div className="flex flex-col gap-1">
          <label htmlFor="quiz-topic">Topic</label>
          <select
            id="quiz-topic"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            className="rounded border border-muted bg-bg p-2"
          >
            <option value={ALL_TOPICS}>All topics</option>
            {info.topics.map((t) => (
              <option key={t.objective_id} value={t.objective_id}>
                {t.topic} ({t.question_count})
              </option>
            ))}
          </select>
        </div>
        <button
          type="button"
          disabled={starting}
          onClick={() => start("quiz")}
          className="self-start rounded border border-accent px-4 py-2 font-semibold text-accent disabled:opacity-50"
        >
          Start quiz
        </button>
      </section>

      <section aria-labelledby="mock-heading" className="flex flex-col gap-3 rounded bg-surface p-5">
        <h2 id="mock-heading" className="font-display text-2xl font-bold uppercase">
          Mock exam
        </h2>
        <ul className="list-disc pl-5">
          <li>{info.question_count} questions</li>
          <li>Pass mark {info.pass_percent}%</li>
          <li>
            Time limit {minutes} minutes{" "}
            {timeUnverified && <Badge variant="unverified" />}
          </li>
        </ul>
        <p className="text-sm text-muted">
          Question count and pass mark: {info.source}.
          {timeUnverified &&
            " Transport Canada does not publish a PSTAR time limit; the 90 minutes comes from a third-party source."}{" "}
          Questions are drawn from each section in proportion to its size. That
          is Waypoint&apos;s rule, not how Transport Canada builds the exam.
        </p>
        <button
          type="button"
          disabled={starting}
          onClick={() => start("mock")}
          className="self-start rounded bg-accent px-4 py-2 font-semibold text-on-accent disabled:opacity-50"
        >
          Start mock exam
        </button>
      </section>
    </div>
  );
}
