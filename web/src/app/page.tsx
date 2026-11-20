import Link from "next/link";
import ApiStatus from "@/components/ApiStatus";
import Disclaimer from "@/components/Disclaimer";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-16">
      <h1 className="text-4xl font-semibold tracking-tight">Waypoint</h1>
      <p className="text-lg">
        Canadian pilot training and exam preparation.
      </p>
      <ApiStatus />
      <Link href="/learn" className="text-sky underline">
        Ask the instructor
      </Link>
      <Disclaimer />
    </main>
  );
}
