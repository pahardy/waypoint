ALTER TABLE objective ADD COLUMN detail text;

CREATE TABLE flight_test_checklist (
    objective_id text PRIMARY KEY REFERENCES objective (id),
    reviewed boolean NOT NULL,
    note text NOT NULL,
    updated_at timestamptz NOT NULL
);
