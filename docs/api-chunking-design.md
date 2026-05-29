# RAG API and Chunking MVP

## Boundary

`plozen-knowledge` owns the knowledge engine:

- document ingest
- Markdown/text chunking
- embedding generation
- pgvector storage
- semantic search
- search audit logs

`plozen-console` should call this API and render the Knowledge Center UI. It should not write directly to the knowledge database.

## MVP API

```text
GET  /health
POST /documents/ingest
POST /documents/upload
GET  /documents
GET  /documents/{source_id}/chunks
POST /search
GET  /search/audit-logs
```

## Ingest Flow

```text
Markdown/text input
  -> source_hash 계산
  -> 기존 source_uri 확인
  -> 변경 없음이면 skip
  -> Markdown heading/paragraph 기준 chunking
  -> chunk embedding 생성
  -> document_sources upsert
  -> 기존 document_chunks 교체
  -> 새 document_chunks insert
```

## Search Flow

```text
query text
  -> query embedding 생성
  -> pgvector cosine distance search
  -> top-k chunks 반환
  -> search_audit_logs 기록
```

## Idempotency

The first MVP uses `source_uri + source_hash`.

- Same URI and same hash: skip ingest.
- Same URI and changed hash: update source metadata, replace chunks.

This keeps repeated Obsidian/file ingest runs from accumulating duplicate chunks.

For uploaded files without an explicit `source_uri`, the API generates `upload://{content_hash_prefix}/{filename}`. This avoids overwriting unrelated uploads that happen to share the same filename.

## Embedding Provider

The implementation supports two providers:

```text
fake
  Local deterministic keyword-hash vector.
  Used for tests and no-cost smoke tests.

openai
  Calls the OpenAI Embeddings API.
  Requires OPENAI_API_KEY.
```

The current database uses `vector(1536)`, so the provider output must be 1536 dimensions.

## Console Relationship

Branding can present this as:

```text
PLOZEN Console > Knowledge Center
```

Implementation should remain:

```text
plozen-console UI
  -> plozen-knowledge API
  -> PostgreSQL + pgvector
```

This keeps the RAG engine reusable by Console, MCP, agents, n8n, and future apps.

## API Access Guard

`/health` is public for service checks. Other endpoints require `KNOWLEDGE_API_KEY` by default and expect the same value in `X-Knowledge-Api-Key`.

The example environment file intentionally leaves secret values empty. Real secrets stay in local/server `.env` files and must not be committed. Local unauthenticated testing requires an explicit `ALLOW_UNAUTHENTICATED_DEV=true`.
