import type { Metadata } from "next";
import Disclaimer from "@/components/Disclaimer";
import PracticeMenu from "@/components/PracticeMenu";

export const metadata: Metadata = { title: "Practice | Waypoint" };

export default function Practice() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
      <h1 className="font-display text-4xl font-bold uppercase tracking-wide">
        Practice
      </h1>
      <PracticeMenu exam="PSTAR" />
      <PracticeMenu exam="PPAER" />
      <footer className="mt-auto border-t border-surface pt-4">
        <Disclaimer />
      </footer>
    </main>
  );
}
