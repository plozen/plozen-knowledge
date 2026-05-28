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
  ingest, search, health check를 담당할 예정인 FastAPI 서비스.

plozen-knowledge-mcp-server
  search_knowledge 같은 tool을 제공할 예정인 MCP server.
```

## 데이터 모델 계획

```text
document_sources
  Markdown note 같은 원본 문서 1개를 나타내는 테이블.

document_chunks
  검색 가능한 text chunk, vector embedding, metadata를 저장하는 테이블.

search_audit_logs
  포트폴리오 증거와 debugging을 위한 query/tool 사용 로그.
```

## 설계 메모

- Obsidian은 원문 source of truth로 유지합니다.
- RAG 데이터는 원문에서 파생된 검색 index입니다.
- RAG 시스템은 Obsidian 원문 note를 수정하지 않습니다.
- PostgreSQL은 관계형 metadata와 vector embedding을 함께 저장합니다.
- pgvector는 SQL에서 cosine similarity search를 가능하게 합니다.
