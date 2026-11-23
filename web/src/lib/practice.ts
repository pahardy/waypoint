/** Quizzes and mock exams: the /exams and /attempts endpoints. */

import { API_URL } from "@/lib/chat";

export type Topic = { objective_id: string; topic: string; question_count: number };

export type ExamInfo = {
  exam: string;
  question_count: number;
  time_limit_s: number;
  pass_percent: number;
  source: string;
  unverified: string[];
  quiz_length: number;
  topics: Topic[];
};

export type Kind = "quiz" | "mock";

export type AttemptQuestion = {
  position: number;
  question_id: string;
  number: string | null;
  objective_id: string;
  topic: string;
  stem: string;
  choices: string[];
  origin: "official" | "generated";
  chosen_index: number | null;
};

export type Attempt = {
  id: string;
  kind: Kind;
  exam: string;
  started_at: string;
  deadline: string | null;
  submitted_at: string | null;
  questions: AttemptQuestion[];
};

export type ReviewItem = AttemptQuestion & { answer_index: number; correct: boolean };

export type TopicScore = {
  objective_id: string;
  topic: string;
  correct: number;
  total: number;
};

export type Results = {
  id: string;
  kind: Kind;
  exam: string;
  correct: number;
  total: number;
  pass_percent: number;
  passed: boolean;
  submitted_at: string;
  topics: TopicScore[];
  review: ReviewItem[];
};

/** Thrown when the API refuses a request; `status` is the HTTP status. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json" },
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, body.detail ?? `Request failed (${response.status}).`);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

export const getExam = (exam: string) => request<ExamInfo>(`/exams/${exam}`);

export const startAttempt = (exam: string, kind: Kind, objectiveId: string | null) =>
  request<Attempt>("/attempts", {
    method: "POST",
    body: JSON.stringify({ exam, kind, objective_id: objectiveId }),
  });

export const getAttempt = (id: string) => request<Attempt>(`/attempts/${id}`);

export const answer = (id: string, position: number, chosenIndex: number) =>
  request<void>(`/attempts/${id}/answers`, {
    method: "POST",
    body: JSON.stringify({ position, chosen_index: chosenIndex }),
  });

export const submit = (id: string) =>
  request<Results>(`/attempts/${id}/submit`, { method: "POST" });

export const getResults = (id: string) => request<Results>(`/attempts/${id}/results`);

/** Seconds as m:ss, or h:mm:ss from an hour up. */
export function clockText(seconds: number): string {
  const s = Math.max(0, Math.ceil(seconds));
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const ss = String(s % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${ss}` : `${m}:${ss}`;
}
