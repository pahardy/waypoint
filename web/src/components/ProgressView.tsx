"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { SUBJECTS, startAttempt } from "@/lib/practice";
import { type Progress, type WeakObjective, getProgress } from "@/lib/progress";

const EXAMS = ["PSTAR", "PPAER"] as const;

/** One exam's answers so far per subject, and its weak objectives with the
 * numbers behind each. */
export default function ProgressView() {
  const [exam, setExam] = useState<string>("PSTAR");
  const [progress, setProgress] = useState<Progress | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getProgress(exam)
      .then((p) => {
        setProgress(p);
        setError(null);
      })
      .catch(() => setError("Progress could not be loaded."));
  }, [exam]);

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1 self-start">
        <label htmlFor="progress-exam">Exam</label>
        <select
          id="progress-exam"
          value={exam}
          onChange={(e) => setExam(e.target.value)}
          className="rounded border border-muted bg-bg p-2"
        >
          {EXAMS.map((e) => (
            <option key={e} value={e}>
              {e}
            </option>
          ))}
        </select>
      </div>
      {error ? (
        <p role="alert" className="text-fail">{error}</p>
      ) : !progress || progress.exam !== exam ? (
        <p role="status">Loading...</p>
      ) : (
        <ExamProgress progress={progress} />
      )}
    </div>
  );
}

function ExamProgress({ progress }: { progress: Progress }) {
  if (progress.subjects.every((s) => s.seen === 0)) {
    return <p>No {progress.exam} questions answered yet. Take a quiz to see progress here.</p>;
  }
  return (
    <>
      <StudyNext progress={progress} />
      <section aria-labelledby="progress-subjects-heading" className="flex flex-col gap-3">
        <h2 id="progress-subjects-heading" className="font-display text-2xl font-bold uppercase">
          By subject
        </h2>
        <table aria-labelledby="progress-subjects-heading" className="w-full text-left">
          <thead className="text-sm text-muted">
            <tr>
              <th scope="col" className="py-1">Subject</th>
              <th scope="col" className="py-1 text-right">Correct</th>
              <th scope="col" className="py-1 text-right">Seen</th>
              <th scope="col" className="py-1 text-right">Percent</th>
            </tr>
          </thead>
          <tbody>
            {progress.subjects.map((s) => (
              <tr key={s.subject} className="border-t border-surface">
                <td className="py-2">{SUBJECTS[s.subject] ?? s.subject}</td>
                <td className="py-2 text-right font-mono">{s.correct}</td>
                <td className="py-2 text-right font-mono">{s.seen}</td>
                <td className="py-2 text-right font-mono">
                  {s.percent === null ? "None seen" : `${s.percent}%`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      {progress.weak.length > 0 && (
        <details className="rounded bg-surface p-4">
          <summary className="cursor-pointer font-semibold">
            All weak objectives ({progress.weak.length})
          </summary>
          <p className="mt-2 text-muted">
            Objectives answered at least 5 times and below the {progress.pass_percent}% pass
            mark, lowest first.
          </p>
          <ul className="mt-2 flex flex-col gap-2">
            {progress.weak.map((w) => (
              <li key={w.objective_id}>
                <p className="font-semibold">{w.topic}</p>
                <p>{w.reason}</p>
              </li>
            ))}
          </ul>
        </details>
      )}
    </>
  );
}

/** The weakest objectives, each with its reason and a topic quiz to start. */
function StudyNext({ progress }: { progress: Progress }) {
  const router = useRouter();
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function start(objective: WeakObjective) {
    setStarting(true);
    try {
      const attempt = await startAttempt(progress.exam, "quiz", objective.objective_id);
      router.push(`/practice/${attempt.id}`);
    } catch (e) {
      setError((e as Error).message);
      setStarting(false);
    }
  }

  return (
    <section aria-labelledby="study-next-heading" className="flex flex-col gap-3">
      <h2 id="study-next-heading" className="font-display text-2xl font-bold uppercase">
        Study next
      </h2>
      {error && <p role="alert" className="text-fail">{error}</p>}
      {progress.recommendations.length === 0 ? (
        <p>
          No weak objectives at the moment. Try a mixed quiz from{" "}
          <Link href="/practice" className="text-sky underline">
            Practice
          </Link>
          .
        </p>
      ) : (
        <ul className="flex flex-col gap-2">
          {progress.recommendations.map((r) => (
            <li key={r.objective_id}>
              <section
                aria-label={r.topic}
                className="flex flex-col gap-2 rounded bg-surface p-4"
              >
                <p className="font-semibold">{r.topic}</p>
                <p>{r.reason}</p>
                <button
                  type="button"
                  disabled={starting}
                  onClick={() => start(r)}
                  className="self-start rounded border border-accent px-4 py-2 font-semibold text-accent disabled:opacity-50"
                >
                  Start quiz
                </button>
              </section>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
