import type { Metadata } from "next";
import Disclaimer from "@/components/Disclaimer";
import ProgressView from "@/components/ProgressView";

export const metadata: Metadata = { title: "Dashboard | Waypoint" };

export default function Dashboard() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
      <h1 className="font-display text-4xl font-bold uppercase tracking-wide">
        Dashboard
      </h1>
      <p className="text-muted">
        Your quiz and mock exam answers so far, per subject and objective.
      </p>
      <ProgressView />
      <footer className="mt-auto border-t border-surface pt-4">
        <Disclaimer />
      </footer>
    </main>
  );
}
