import type { Metadata } from "next";
import Disclaimer from "@/components/Disclaimer";
import ExerciseMenu from "@/components/ExerciseMenu";
import { SIMULATION } from "@/lib/exercises";

export const metadata: Metadata = { title: "Exercises | Waypoint" };

export default function Exercises() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
      <h1 className="font-display text-4xl font-bold uppercase tracking-wide">
        Exercises
      </h1>
      <p className="font-semibold">{SIMULATION}</p>
      <p className="text-muted">
        Explain a concept or work through a situation in your own words. Each
        answer is graded against a rubric, with the words it was graded on.
      </p>
      <ExerciseMenu />
      <footer className="mt-auto border-t border-surface pt-4">
        <Disclaimer />
      </footer>
    </main>
  );
}
