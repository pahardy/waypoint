CREATE TABLE document (
    id text PRIMARY KEY,
    title text NOT NULL,
    publisher text NOT NULL,
    tp_number text,
    edition text NOT NULL,
    published text NOT NULL,
    retrieved_on date NOT NULL,
    jurisdiction text NOT NULL CHECK (jurisdiction IN ('CA', 'non-CA')),
    url text NOT NULL,
    sha256 text NOT NULL
);

CREATE TABLE chunk (
    id text PRIMARY KEY,
    document_id text NOT NULL REFERENCES document (id) ON DELETE CASCADE,
    section_ref text NOT NULL,
    heading_path text[] NOT NULL,
    page integer NOT NULL,
    text text NOT NULL,
    token_count integer NOT NULL,
    embedding_model text NOT NULL,
    embedding vector(1024) NOT NULL
);

CREATE INDEX chunk_document_idx ON chunk (document_id);
CREATE INDEX chunk_embedding_idx ON chunk USING hnsw (embedding vector_cosine_ops);
