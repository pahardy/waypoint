import ApiStatus from "@/components/ApiStatus";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-16">
      <h1 className="text-4xl font-semibold tracking-tight">Waypoint</h1>
      <p className="text-lg">
        Canadian pilot training and exam preparation.
      </p>
      <ApiStatus />
      <p className="text-sm opacity-70">
        Waypoint is an educational aid. It does not replace flight
        instruction, an authorized examiner or current Transport Canada
        publications.
      </p>
    </main>
  );
}
