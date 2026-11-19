ALTER TABLE chunk ADD COLUMN search tsvector;

CREATE FUNCTION chunk_search_vector(heading_path text[], body text) RETURNS tsvector
LANGUAGE sql IMMUTABLE AS $$
    SELECT setweight(to_tsvector('english', array_to_string(heading_path, ' ')), 'A')
        || setweight(to_tsvector('english', body), 'B')
$$;

CREATE FUNCTION chunk_set_search() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    NEW.search := chunk_search_vector(NEW.heading_path, NEW.text);
    RETURN NEW;
END
$$;

CREATE TRIGGER chunk_search_update BEFORE INSERT OR UPDATE OF heading_path, text
ON chunk FOR EACH ROW EXECUTE FUNCTION chunk_set_search();

UPDATE chunk SET search = chunk_search_vector(heading_path, text);
ALTER TABLE chunk ALTER COLUMN search SET NOT NULL;
CREATE INDEX chunk_search_idx ON chunk USING gin (search);
