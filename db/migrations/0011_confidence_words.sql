ALTER TABLE objective_mastery ALTER COLUMN self_confidence TYPE text;
ALTER TABLE objective_mastery ADD CONSTRAINT objective_mastery_self_confidence_check
    CHECK (self_confidence IN ('low', 'medium', 'high'));
