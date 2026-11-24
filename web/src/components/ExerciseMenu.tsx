"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { type ExerciseSummary, listExercises, startSession } from "@/lib/exercises";

const KIND_LABELS = { oral: "Oral question", scenario: "Scenario" } as const;

/** An exercise's name from its id: "deteriorating-weather" is
 * "Deteriorating weather". */
export function exerciseName(id: string): string {
  const words = id.replaceAll("-", " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/** Every oral exercise and scenario, each with a button that starts a session. */
export default function ExerciseMenu() {
  const router = useRouter();
  const [exercises, setExercises] = useState<ExerciseSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    listExercises()
      .then(setExercises)
      .catch(() => setError("The exercises could not be loaded."));
  }, []);

  async function start(id: string) {
    setStarting(true);
    try {
      const session = await startSession(id);
      router.push(`/exercises/${session.id}`);
    } catch (e) {
      setError((e as Error).message);
      setStarting(false);
    }
  }

  if (error) return <p role="alert" className="text-fail">{error}</p>;
  if (!exercises) return <p role="status">Loading...</p>;

  return (
    <ul className="flex flex-col gap-4">
      {exercises.map((e) => (
        <li key={e.id}>
          <section
            aria-labelledby={`${e.id}-heading`}
            className="flex flex-col gap-3 rounded bg-surface p-5"
          >
            <h2 id={`${e.id}-heading`} className="font-display text-2xl font-bold uppercase">
              {exerciseName(e.id)}
            </h2>
            <p className="text-muted">
              {KIND_LABELS[e.kind]}, {e.exam}
            </p>
            <p>{e.prompt}</p>
            <button
              type="button"
              onClick={() => start(e.id)}
              disabled={starting}
              className="self-start rounded bg-accent px-4 py-2 font-semibold text-on-accent disabled:opacity-50"
            >
              Start
            </button>
          </section>
        </li>
      ))}
    </ul>
  );
}
