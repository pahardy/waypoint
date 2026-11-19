ALTER TABLE document ADD COLUMN exams text[] NOT NULL DEFAULT '{}';
ALTER TABLE chunk ADD COLUMN subject text;
