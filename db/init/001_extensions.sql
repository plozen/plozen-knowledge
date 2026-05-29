CREATE EXTENSION IF NOT EXISTS vector;

\i /docker-entrypoint-initdb.d/migrations/001_rag_schema.sql
