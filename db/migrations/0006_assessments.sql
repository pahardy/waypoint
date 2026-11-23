CREATE TABLE objective (
    id text PRIMARY KEY,
    exam text NOT NULL CHECK (exam IN ('PSTAR', 'PPAER', 'FLIGHT_TEST')),
    subject text NOT NULL,
    area text NOT NULL,
    topic text NOT NULL,
    text text NOT NULL,
    ref text,
    source text NOT NULL,
    page integer NOT NULL
);

CREATE TABLE question (
    id text PRIMARY KEY,
    exam text NOT NULL CHECK (exam IN ('PSTAR', 'PPAER', 'FLIGHT_TEST')),
    objective_id text NOT NULL REFERENCES objective (id),
    number text,
    stem text NOT NULL,
    choices jsonb NOT NULL,
    answer_index integer NOT NULL CHECK (answer_index >= 0),
    explanation text,
    source text NOT NULL,
    page integer,
    source_chunk_id text,
    origin text NOT NULL CHECK (origin IN ('official', 'generated')),
    status text NOT NULL CHECK (status IN ('draft', 'reviewed', 'retired'))
);

CREATE INDEX question_objective_idx ON question (objective_id);

CREATE TABLE attempt (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    kind text NOT NULL CHECK (kind IN ('quiz', 'mock')),
    exam text NOT NULL CHECK (exam IN ('PSTAR', 'PPAER', 'FLIGHT_TEST')),
    started_at timestamptz NOT NULL,
    time_limit_s integer,
    submitted_at timestamptz,
    correct integer,
    total integer NOT NULL,
    passed boolean
);

CREATE TABLE attempt_item (
    attempt_id uuid NOT NULL REFERENCES attempt (id) ON DELETE CASCADE,
    position integer NOT NULL,
    question_id text NOT NULL REFERENCES question (id),
    chosen_index integer,
    answered_at timestamptz,
    PRIMARY KEY (attempt_id, position)
);
