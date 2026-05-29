# PLOZEN Knowledge

PLOZEN이라는 가상 회사의 내부 문서, 프로젝트 기록, 세션 로그를 pgvector 기반 RAG 저장소와 MCP Server로 연결하는 포트폴리오 프로젝트입니다.

이 저장소는 진행 중인 포트폴리오입니다. 먼저 재현 가능한 PostgreSQL + pgvector 스택을 구성하고, 이후 Obsidian/Markdown ingest pipeline, semantic search API, MCP server로 확장합니다.

## 현재 상태

- 13서버에서 PostgreSQL + pgvector 컨테이너 실행 완료
- DB 초기화 SQL로 `vector` extension 활성화
- 기본 vector similarity smoke test 통과
- RAG DB schema migration 작성
- demo knowledge seed와 top-k similarity search smoke SQL 작성
- FastAPI 기반 ingest/search API MVP 작성
- Markdown/text chunking과 fake/OpenAI embedding provider 분리
- MCP server는 다음 단계로 개발 예정

## 목표 MVP

1. PLOZEN knowledge base의 Markdown 문서 10건 ingest
2. 문서를 검색 가능한 chunk로 분리
3. embedding 생성 후 PostgreSQL + pgvector에 저장
4. source metadata와 함께 top-k similarity search 실행
5. MCP server에서 `search_knowledge` tool 제공
6. AX-SI / RAG 포트폴리오 증거 정리

## 기술 스택

- PostgreSQL 16
- pgvector
- Docker Compose
- Python / FastAPI
- MCP Server 예정
- LangChain / LangGraph는 후속 포트폴리오 레이어로 추가 예정

## 로컬 실행

예시 환경변수 파일을 복사합니다.

```bash
cp .env.example .env
```

`.env`의 `POSTGRES_PASSWORD`와 `KNOWLEDGE_API_KEY`는 실제 값으로 설정합니다. 기본 예시는 비워두며, 비밀 값은 커밋하지 않습니다.

DB 컨테이너를 실행합니다. Fresh DB에서는 `db/init/001_extensions.sql`이 pgvector extension과 RAG schema migration을 함께 적용합니다.

```bash
docker compose up -d
```

API까지 함께 실행하려면 같은 명령을 사용합니다. API는 기본적으로 `http://localhost:8100`에서 열립니다.

```bash
docker compose up -d --build
```

컨테이너 상태를 확인합니다.

```bash
docker compose ps
```

PostgreSQL에 접속합니다.

```bash
docker exec -it plozen-knowledge-postgres psql -U plozen -d plozen_knowledge
```

pgvector extension을 확인합니다.

```sql
SELECT extname, extversion
FROM pg_extension
WHERE extname = 'vector';
```

## API 실행

개발 환경에서 직접 실행할 수 있습니다.

```bash
pip install -e ".[dev]"
uvicorn plozen_knowledge_api.main:app --host 0.0.0.0 --port 8100 --reload
```

API 문서는 FastAPI가 자동 생성합니다.

```text
http://localhost:8100/docs
```

`/health`를 제외한 API는 기본적으로 `X-Knowledge-Api-Key` 헤더가 필요합니다. 로컬에서만 인증 없이 시험하려면 `.env`에 `ALLOW_UNAUTHENTICATED_DEV=true`를 명시적으로 설정합니다.

health check:

```bash
curl http://localhost:8100/health
```

문서 ingest:

```bash
curl -X POST http://localhost:8100/documents/ingest \
  -H "Content-Type: application/json" \
  -H "X-Knowledge-Api-Key: $KNOWLEDGE_API_KEY" \
  -d '{
    "source_type": "manual_note",
    "source_uri": "manual://rag-api-smoke",
    "title": "RAG API Smoke",
    "content": "# RAG API\n\nPLOZEN Knowledge는 문서를 청킹하고 embedding으로 pgvector 검색을 수행합니다.",
    "metadata": {"project": "PLOZEN Knowledge"}
  }'
```

검색:

```bash
curl -X POST http://localhost:8100/search \
  -H "Content-Type: application/json" \
  -H "X-Knowledge-Api-Key: $KNOWLEDGE_API_KEY" \
  -d '{"query": "PLOZEN Knowledge RAG 검색", "top_k": 3}'
```

## RAG schema smoke test

기존 DB에 RAG schema를 반영합니다.

```bash
docker exec -i plozen-knowledge-postgres psql -U plozen -d plozen_knowledge < db/migrations/001_rag_schema.sql
```

demo knowledge chunk 10건을 적재합니다. 이 seed는 외부 embedding API 없이 pgvector 검색 흐름을 검증하기 위한 deterministic vector를 사용합니다.

```bash
docker exec -i plozen-knowledge-postgres psql -U plozen -d plozen_knowledge < db/seeds/001_demo_knowledge.sql
```

similarity search smoke test를 실행합니다.

```bash
docker exec -i plozen-knowledge-postgres psql -U plozen -d plozen_knowledge < db/smoke/001_similarity_search.sql
```

예상 확인 포인트:

- `document_sources` 4건 이상
- `document_chunks` 10건 이상
- `search_audit_logs`에 `manual_sql_smoke` 로그 1건 이상
- top-k 결과에 source title, chunk index, cosine distance, preview가 표시됨

실행 증거는 `docs/smoke-2026-05-29.md`에 기록했습니다.

## 저장소 구조

```text
db/init/                 DB 최초 생성 시 실행되는 초기화 SQL
db/migrations/           RAG schema migration
db/seeds/                demo knowledge seed
db/smoke/                SQL smoke tests
docs/                    아키텍처와 포트폴리오 문서
docker-compose.yml       로컬/서버 재현 실행 정의
.env.example             공개용 환경변수 예시
src/plozen_knowledge_api FastAPI 기반 RAG API
tests/                   chunking/embedding unit tests
```

추가 예정 구조:

```text
apps/mcp-server/         에이전트 접근용 MCP tools
```
