"use client";

import Link from "next/link";
import { useEffect, useId, useState } from "react";
import CitationChip from "@/components/CitationChip";
import { exerciseName } from "@/components/ExerciseMenu";
import SourceDetail from "@/components/SourceDetail";
import { type ChecklistEntry, type ChecklistItem, getChecklist, saveEntry } from "@/lib/flightTest";

/** The TP 13723 items grouped by exercise, each a checklist row the student
 * can mark reviewed and annotate. */
export default function FlightTestChecklist() {
  const [items, setItems] = useState<ChecklistItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getChecklist()
      .then(setItems)
      .catch(() => setError("The checklist could not be loaded."));
  }, []);

  if (error) return <p role="alert" className="text-fail">{error}</p>;
  if (!items) return <p role="status">Loading...</p>;

  function update(objectiveId: string, entry: ChecklistEntry) {
    setItems((current) =>
      current!.map((i) => (i.objective_id === objectiveId ? { ...i, ...entry } : i)),
    );
  }

  const exercises = [...new Set(items.map((i) => i.exercise))];
  const reviewed = items.filter((i) => i.reviewed).length;

  return (
    <div className="flex flex-col gap-6">
      <p className="font-semibold">
        {reviewed} of {items.length} items marked reviewed
      </p>
      {exercises.map((exercise) => (
        <section key={exercise} aria-label={exercise} className="flex flex-col gap-2">
          <h2 className="font-display text-xl font-bold uppercase">{exercise}</h2>
          <ul className="flex flex-col gap-2">
            {items
              .filter((i) => i.exercise === exercise)
              .map((i) => (
                <li key={i.objective_id}>
                  <ChecklistRow item={i} onChange={update} />
                </li>
              ))}
          </ul>
        </section>
      ))}
    </div>
  );
}

type RowProps = {
  item: ChecklistItem;
  onChange: (objectiveId: string, entry: ChecklistEntry) => void;
};

function ChecklistRow({ item, onChange }: RowProps) {
  const [note, setNote] = useState(item.note);
  const [sourceOpen, setSourceOpen] = useState(false);
  const [error, setError] = useState(false);
  const id = useId();
  const status = item.reviewed ? "REVIEWED" : "TO REVIEW";

  /** Show the entry at once; put the previous one back if saving fails. */
  async function save(entry: ChecklistEntry) {
    const previous = { reviewed: item.reviewed, note: item.note };
    onChange(item.objective_id, entry);
    try {
      await saveEntry(item.objective_id, entry);
      setError(false);
    } catch {
      onChange(item.objective_id, previous);
      setError(true);
    }
  }

  return (
    <details className="rounded bg-surface p-3">
      <summary className="flex cursor-pointer items-baseline gap-2 font-mono text-sm">
        <span className="font-sans text-base">{item.title}</span>
        <span aria-hidden="true" className="flex-1 border-b-2 border-dotted border-muted" />
        <span className={item.reviewed ? "text-pass" : "text-muted"}>{status}</span>
      </summary>
      <div className="mt-3 flex flex-col gap-3">
        {item.aim && (
          <p>
            <span className="font-semibold">Aim: </span>
            {item.aim}
          </p>
        )}
        {item.source && (
          <div>
            <CitationChip
              citation={item.source}
              open={sourceOpen}
              detailId={`${id}-source`}
              onToggle={() => setSourceOpen(!sourceOpen)}
            />
            <div id={`${id}-source`}>{sourceOpen && <SourceDetail citation={item.source} />}</div>
          </div>
        )}
        {item.exercise_ids.length > 0 && (
          <p>
            Practise:{" "}
            {item.exercise_ids.map((e, n) => (
              <span key={e}>
                {n > 0 && ", "}
                <Link href="/exercises" className="text-sky underline">
                  {exerciseName(e)}
                </Link>
              </span>
            ))}
          </p>
        )}
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={item.reviewed}
            onChange={(e) => save({ reviewed: e.target.checked, note })}
            className="size-5"
          />
          Reviewed
        </label>
        <div className="flex flex-col gap-1">
          <label htmlFor={`${id}-note`}>Questions for my instructor</label>
          <textarea
            id={`${id}-note`}
            value={note}
            maxLength={500}
            rows={2}
            onChange={(e) => setNote(e.target.value)}
            onBlur={() => note !== item.note && save({ reviewed: item.reviewed, note })}
            className="rounded border border-muted bg-bg p-2"
          />
        </div>
        {error && (
          <p role="alert" className="text-sm text-fail">
            Not saved.
          </p>
        )}
      </div>
    </details>
  );
}
