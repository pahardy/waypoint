CREATE TABLE objective_mastery (
    objective_id text PRIMARY KEY REFERENCES objective (id),
    correct integer NOT NULL CHECK (correct >= 0),
    seen integer NOT NULL CHECK (seen >= correct),
    last_seen_at timestamptz NOT NULL,
    self_confidence smallint
);

INSERT INTO objective_mastery (objective_id, correct, seen, last_seen_at)
SELECT q.objective_id,
       count(*) FILTER (WHERE i.chosen_index = q.answer_index),
       count(*),
       max(a.submitted_at)
FROM attempt a
JOIN attempt_item i ON i.attempt_id = a.id
JOIN question q ON q.id = i.question_id
WHERE a.submitted_at IS NOT NULL
GROUP BY q.objective_id;
