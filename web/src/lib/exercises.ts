/** Oral exercises and scenarios: the /exercises and /sessions endpoints. */

import { request } from "@/lib/practice";

export const SIMULATION = "Educational simulation. Not operational guidance.";

export type ExerciseSummary = {
  id: string;
  kind: "oral" | "scenario";
  exam: string;
  prompt: string;
};

export type StageView = { index: number; id: string; facts: string[]; question: string };

export type Mark = "met" | "partly_met" | "not_met";

export type GradedMark = {
  criterion_id: string;
  description: string;
  weight: number;
  mark: Mark;
  evidence: string;
  reason: string;
};

export type GradedStage = {
  index: number;
  id: string;
  question: string;
  answer: string;
  marks: GradedMark[];
  score: number;
};

export type Session = {
  id: string;
  exercise_id: string;
  kind: "oral" | "scenario";
  exam: string;
  intro: string | null;
  synthetic_notice: string | null;
  stage_count: number;
  current: StageView | null;
  revealed: string[];
  graded: GradedStage[];
  overall_score: number | null;
};

export const MARK_LABELS: Record<Mark, string> = {
  met: "Met",
  partly_met: "Partly met",
  not_met: "Not met",
};

export const listExercises = () => request<ExerciseSummary[]>("/exercises");

export const startSession = (exerciseId: string) =>
  request<Session>("/sessions", {
    method: "POST",
    body: JSON.stringify({ exercise_id: exerciseId }),
  });

export const getSession = (id: string) => request<Session>(`/sessions/${id}`);

export const answerStage = (id: string, answer: string) =>
  request<Session>(`/sessions/${id}/answers`, {
    method: "POST",
    body: JSON.stringify({ answer }),
  });
