import type { Metadata } from "next";
import { Suspense } from "react";
import AttemptRunner from "@/components/AttemptRunner";

export const metadata: Metadata = { title: "Practice | Waypoint" };

export default function AttemptPage({ params }: PageProps<"/practice/[attemptId]">) {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
      <h1 className="font-display text-4xl font-bold uppercase tracking-wide">
        Practice
      </h1>
      <Suspense fallback={<p role="status">Loading...</p>}>
        {params.then(({ attemptId }) => (
          <AttemptRunner attemptId={attemptId} />
        ))}
      </Suspense>
    </main>
  );
}
