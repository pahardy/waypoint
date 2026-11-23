import type { Metadata } from "next";
import { Suspense } from "react";
import Disclaimer from "@/components/Disclaimer";
import ResultsView from "@/components/ResultsView";

export const metadata: Metadata = { title: "Results | Waypoint" };

export default function ResultsPage({ params }: PageProps<"/results/[attemptId]">) {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
      <h1 className="font-display text-4xl font-bold uppercase tracking-wide">
        Results
      </h1>
      <Suspense fallback={<p role="status">Loading...</p>}>
        {params.then(({ attemptId }) => (
          <ResultsView attemptId={attemptId} />
        ))}
      </Suspense>
      <footer className="mt-auto border-t border-surface pt-4">
        <Disclaimer />
      </footer>
    </main>
  );
}
