ALTER TABLE attempt ADD COLUMN outcome text
    CHECK (outcome IN ('pass', 'partial', 'fail'));
