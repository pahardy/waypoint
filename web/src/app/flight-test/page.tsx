import type { Metadata } from "next";
import Disclaimer from "@/components/Disclaimer";
import FlightTestChecklist from "@/components/FlightTestChecklist";
import { NOT_READINESS } from "@/lib/flightTest";

export const metadata: Metadata = { title: "Flight test | Waypoint" };

export default function FlightTest() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
      <h1 className="font-display text-4xl font-bold uppercase tracking-wide">
        Flight test
      </h1>
      <p className="text-muted">
        Each item of the PPL-A flight test guide (TP 13723), with its aim and the
        guide page. Mark what you have reviewed and note questions for your
        instructor.
      </p>
      <p className="font-semibold">{NOT_READINESS}</p>
      <FlightTestChecklist />
      <footer className="mt-auto border-t border-surface pt-4">
        <Disclaimer />
      </footer>
    </main>
  );
}
