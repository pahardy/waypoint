import type { Metadata } from "next";
import Chat from "@/components/Chat";
import Disclaimer from "@/components/Disclaimer";

export const metadata: Metadata = { title: "Learn | Waypoint" };

export default function Learn() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
      <h1 className="font-display text-4xl font-bold uppercase tracking-wide">
        Ask the instructor
      </h1>
      <p className="text-muted">
        Answers come from Transport Canada publications, the Canadian Aviation
        Regulations and FAA handbooks, with the source of each fact cited.
      </p>
      <Chat />
      <footer className="mt-auto border-t border-surface pt-4">
        <Disclaimer />
      </footer>
    </main>
  );
}
