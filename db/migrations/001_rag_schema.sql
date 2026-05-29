CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS document_sources (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_type text NOT NULL,
  source_uri text NOT NULL UNIQUE,
  title text NOT NULL,
  source_hash text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  ingested_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS document_chunks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id uuid NOT NULL REFERENCES document_sources(id) ON DELETE CASCADE,
  chunk_index integer NOT NULL,
  content text NOT NULL,
  token_count integer NOT NULL DEFAULT 0,
  embedding vector(1536) NOT NULL,
  content_hash text NOT NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source_id, chunk_index)
);

CREATE TABLE IF NOT EXISTS search_audit_logs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  query_text text NOT NULL,
  query_embedding vector(1536),
  tool_name text NOT NULL DEFAULT 'manual_sql_smoke',
  top_k integer NOT NULL DEFAULT 5,
  match_count integer NOT NULL DEFAULT 0,
  filters jsonb NOT NULL DEFAULT '{}'::jsonb,
  latency_ms integer,
  result_chunk_ids uuid[] NOT NULL DEFAULT ARRAY[]::uuid[],
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_document_sources_type
  ON document_sources (source_type);

CREATE INDEX IF NOT EXISTS idx_document_sources_metadata
  ON document_sources USING gin (metadata);

CREATE INDEX IF NOT EXISTS idx_document_chunks_source
  ON document_chunks (source_id, chunk_index);

CREATE INDEX IF NOT EXISTS idx_document_chunks_metadata
  ON document_chunks USING gin (metadata);

CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding_hnsw
  ON document_chunks USING hnsw (embedding vector_cosine_ops);

CREATE INDEX IF NOT EXISTS idx_search_audit_logs_created_at
  ON search_audit_logs (created_at DESC);
