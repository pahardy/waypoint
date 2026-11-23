import type { Metadata } from "next";
import Disclaimer from "@/components/Disclaimer";
import PracticeMenu from "@/components/PracticeMenu";

export const metadata: Metadata = { title: "Practice | Waypoint" };

export default function Practice() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
      <h1 className="font-display text-4xl font-bold uppercase tracking-wide">
        PSTAR practice
      </h1>
      <p className="text-muted">
        Official questions from the Transport Canada PSTAR study guide (TP 11919,
        7th edition), scored against its answer key.
      </p>
      <PracticeMenu />
      <footer className="mt-auto border-t border-surface pt-4">
        <Disclaimer />
      </footer>
    </main>
  );
}
