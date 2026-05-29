# 아키텍처

## 목표

PLOZEN Knowledge는 회사 기록, 프로젝트 노트, 세션 로그, 완료된 Todo archive를 검색 가능한 조직 기억 시스템으로 만드는 프로젝트입니다.

## 흐름

```text
Obsidian / Markdown
  -> chunking
  -> embedding
  -> PostgreSQL + pgvector
  -> similarity search
  -> API / MCP Server
  -> agent answer with source metadata
```

## 실행 구성요소

```text
plozen-knowledge-postgres
  pgvector가 포함된 PostgreSQL 16 컨테이너.

plozen-knowledge-api
  ingest, chunking, embedding, search, health check를 담당하는 FastAPI 서비스.

plozen-knowledge-mcp-server
  search_knowledge 같은 tool을 제공할 예정인 MCP server.
```

## 데이터 모델 계획

```text
document_sources
  Markdown note 같은 원본 문서 1개를 나타내는 테이블.
  source_type, source_uri, title, source_hash, metadata, ingested_at을 저장한다.

document_chunks
  검색 가능한 text chunk, vector(1536) embedding, token_count, metadata를 저장하는 테이블.
  source_id와 chunk_index로 원문 내 위치를 복원한다.

search_audit_logs
  포트폴리오 증거와 debugging을 위한 query/tool 사용 로그.
  query_text, tool_name, top_k, match_count, result_chunk_ids를 저장한다.
```

## 1차 구현 범위

- `db/migrations/001_rag_schema.sql`
  - `document_sources`
  - `document_chunks`
  - `search_audit_logs`
  - pgvector cosine search용 HNSW index
- `db/seeds/001_demo_knowledge.sql`
  - Obsidian 세션, PLOZEN Knowledge MOC, Todo card, architecture 문서 기준 demo chunk 10건
  - 외부 embedding API 없이 smoke test 가능한 deterministic vector 사용
- `db/smoke/001_similarity_search.sql`
  - query vector 생성
  - top-k similarity search
  - `search_audit_logs` 기록
- `src/plozen_knowledge_api`
  - FastAPI 기반 `/documents/ingest`, `/documents/upload`, `/search`
  - Markdown heading/paragraph 기반 chunking
  - fake/OpenAI embedding provider 분리
  - source hash 기반 멱등 ingest

## API 경계

```text
PLOZEN Console
  -> plozen-knowledge-api
  -> PostgreSQL + pgvector
```

Console은 Knowledge Center UI를 담당하고, `plozen-knowledge-api`는 RAG 엔진을 담당합니다. Console, MCP server, agent, n8n workflow는 DB에 직접 접근하지 않고 API 또는 MCP tool을 통해 지식 저장소를 사용합니다.

## 설계 메모

- Obsidian은 원문 source of truth로 유지합니다.
- RAG 데이터는 원문에서 파생된 검색 index입니다.
- RAG 시스템은 Obsidian 원문 note를 수정하지 않습니다.
- PostgreSQL은 관계형 metadata와 vector embedding을 함께 저장합니다.
- pgvector는 SQL에서 cosine similarity search를 가능하게 합니다.
