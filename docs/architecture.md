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

## 포트폴리오 확장 로드맵

1차는 pgvector 기반 Vector RAG로 완성합니다.

```text
문서
  -> chunk
  -> embedding
  -> pgvector similarity search
  -> LangChain RAG answer
```

이후 GraphRAG를 별도 확장 레이어로 붙입니다.

```text
chunk
  -> entity extraction
  -> relationship extraction
  -> Neo4j graph storage
  -> community / subgraph summary
```

최종 포트폴리오 목표는 Hybrid RAG입니다.

```text
사용자 질문
  -> pgvector로 의미상 가까운 chunk 후보 검색
  -> Neo4j로 관련 entity/relationship 확장
  -> LangGraph로 검색 품질 평가, 재검색, 답변 검증
  -> source metadata와 graph 근거를 함께 반환
```

이 구조에서 pgvector는 의미 유사도 검색을 담당하고, Neo4j/GraphRAG는 프로젝트, 기술, 문서, 에이전트, 의사결정 사이의 관계 탐색을 담당합니다.

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
- GraphRAG는 1차 필수 범위가 아니라 포트폴리오 확장 단계로 둡니다.
- 최종 Hybrid RAG에서는 pgvector 검색 결과와 Neo4j 관계 그래프를 함께 사용합니다.
