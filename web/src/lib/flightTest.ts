/** The flight-test study companion: the /flight-test endpoints. */

import type { Citation } from "@/lib/chat";
import { request } from "@/lib/practice";

export const NOT_READINESS =
  "Marking items reviewed does not mean you are ready for, or will pass, the flight test. Your instructor and the examiner decide that.";

export type ChecklistEntry = { reviewed: boolean; note: string };

export type ChecklistItem = ChecklistEntry & {
  objective_id: string;
  exercise: string;
  title: string;
  aim: string | null;
  reference: string | null;
  source: Citation | null;
  exercise_ids: string[];
};

export const getChecklist = () => request<ChecklistItem[]>("/flight-test");

export const saveEntry = (objectiveId: string, entry: ChecklistEntry) =>
  request<void>(`/flight-test/${objectiveId}`, {
    method: "PUT",
    body: JSON.stringify(entry),
  });
