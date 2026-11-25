/** Progress per subject and weak objectives: the /progress endpoint. */

import { request } from "@/lib/practice";

export type SubjectProgress = {
  subject: string;
  correct: number;
  seen: number;
  percent: number | null;
};

export type WeakObjective = {
  objective_id: string;
  topic: string;
  correct: number;
  seen: number;
  percent: number;
  reason: string;
};

export type Progress = {
  exam: string;
  pass_percent: number;
  subjects: SubjectProgress[];
  weak: WeakObjective[];
  recommendations: WeakObjective[];
};

export const getProgress = (exam: string) => request<Progress>(`/progress/${exam}`);
