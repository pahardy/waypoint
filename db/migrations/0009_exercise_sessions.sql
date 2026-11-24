CREATE TABLE exercise_session (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    exercise_id text NOT NULL,
    stage_index integer NOT NULL DEFAULT 0 CHECK (stage_index >= 0),
    started_at timestamptz NOT NULL,
    finished_at timestamptz
);

CREATE TABLE stage_answer (
    session_id uuid NOT NULL REFERENCES exercise_session (id),
    stage_index integer NOT NULL CHECK (stage_index >= 0),
    answer text NOT NULL,
    marks jsonb NOT NULL,
    score integer NOT NULL,
    graded_at timestamptz NOT NULL,
    PRIMARY KEY (session_id, stage_index)
);
