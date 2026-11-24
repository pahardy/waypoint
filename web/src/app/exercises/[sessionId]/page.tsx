import type { Metadata } from "next";
import { Suspense } from "react";
import Disclaimer from "@/components/Disclaimer";
import ExerciseRunner from "@/components/ExerciseRunner";
import { SIMULATION } from "@/lib/exercises";

export const metadata: Metadata = { title: "Exercise | Waypoint" };

export default function ExercisePage({ params }: PageProps<"/exercises/[sessionId]">) {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
      <h1 className="font-display text-4xl font-bold uppercase tracking-wide">
        Exercise
      </h1>
      <Suspense fallback={<p role="status">Loading...</p>}>
        {params.then(({ sessionId }) => (
          <ExerciseRunner sessionId={sessionId} />
        ))}
      </Suspense>
      <footer className="mt-auto flex flex-col gap-2 border-t border-surface pt-4">
        <p className="text-sm font-semibold">{SIMULATION}</p>
        <Disclaimer />
      </footer>
    </main>
  );
}
