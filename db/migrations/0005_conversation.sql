CREATE TABLE conversation (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    level text NOT NULL CHECK (level IN ('PSTAR', 'PPAER', 'FLIGHT_TEST')),
    messages jsonb NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
