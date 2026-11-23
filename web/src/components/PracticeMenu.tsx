"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Badge from "@/components/Badge";
import { type ExamInfo, type Kind, getExam, startAttempt } from "@/lib/practice";

const ALL_TOPICS = "";

const QUESTION_SOURCES: Record<string, React.ReactNode> = {
  PSTAR: (
    <>
      <Badge variant="official" /> Questions from the Transport Canada study guide
      (TP 11919, 7th edition), scored against its answer key.
    </>
  ),
  PPAER: (
    <>
      <Badge variant="practice" /> Practice questions written by Waypoint from
      the Canadian Aviation Regulations, the TC AIM and, for facts that are the
      same in every country, FAA handbooks. They are not official Transport
      Canada questions.
    </>
  ),
};

const MOCK_SELECTION: Record<string, string> = {
  PSTAR:
    "Questions are drawn from each TP 11919 section in proportion to its size.",
  PPAER:
    "25 questions from each subject. You need 60% overall and 60% in each subject; 60% overall with a weaker subject is a partial pass.",
};

/** Choose a topic quiz for one exam, or its timed mock exam if it has one. */
export default function PracticeMenu({ exam }: { exam: "PSTAR" | "PPAER" }) {
  const router = useRouter();
  const [info, setInfo] = useState<ExamInfo | null>(null);
  const [topic, setTopic] = useState(ALL_TOPICS);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    getExam(exam)
      .then(setInfo)
      .catch(() => setError("The practice questions could not be loaded."));
  }, [exam]);

  async function start(kind: Kind) {
    setStarting(true);
    try {
      const attempt = await startAttempt(exam, kind, topic || null);
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
      <section
        aria-labelledby={`${exam}-quiz-heading`}
        className="flex flex-col gap-3 rounded bg-surface p-5"
      >
        <h2 id={`${exam}-quiz-heading`} className="font-display text-2xl font-bold uppercase">
          {exam} topic quiz
        </h2>
        <p className="text-muted">{QUESTION_SOURCES[exam]}</p>
        {info.topics.length === 0 ? (
          <p>No reviewed questions yet.</p>
        ) : (
          <>
            <p className="text-muted">
              Up to {info.quiz_length} questions, untimed. Choose one topic or
              mix them all.
            </p>
            <div className="flex flex-col gap-1">
              <label htmlFor={`${exam}-quiz-topic`}>Topic</label>
              <select
                id={`${exam}-quiz-topic`}
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
          </>
        )}
      </section>

      {info.mock_available && (
        <section
          aria-labelledby={`${exam}-mock-heading`}
          className="flex flex-col gap-3 rounded bg-surface p-5"
        >
          <h2 id={`${exam}-mock-heading`} className="font-display text-2xl font-bold uppercase">
            {exam} mock exam
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
              ` Transport Canada does not publish a ${exam} time limit; the ${minutes} minutes comes from a third-party source.`}{" "}
            {MOCK_SELECTION[exam]} The question mix is Waypoint&apos;s rule, not
            how Transport Canada builds the exam.
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
      )}
    </div>
  );
}
