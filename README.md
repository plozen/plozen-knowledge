# PLOZEN Knowledge

PLOZEN이라는 가상 회사의 내부 문서, 프로젝트 기록, 세션 로그를 pgvector 기반 RAG 저장소와 MCP Server로 연결하는 포트폴리오 프로젝트입니다.

이 저장소는 진행 중인 포트폴리오입니다. 먼저 재현 가능한 PostgreSQL + pgvector 스택을 구성하고, 이후 Obsidian/Markdown ingest pipeline, semantic search API, MCP server로 확장합니다.

## 현재 상태

- 13서버에서 PostgreSQL + pgvector 컨테이너 실행 완료
- DB 초기화 SQL로 `vector` extension 활성화
- 기본 vector similarity smoke test 통과
- API, ingest pipeline, MCP server는 다음 단계로 개발 예정

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
- Python / FastAPI 예정
- MCP Server 예정
- LangChain / LangGraph는 후속 포트폴리오 레이어로 추가 예정

## 로컬 실행

예시 환경변수 파일을 복사합니다.

```bash
cp .env.example .env
```

DB 컨테이너를 실행합니다.

```bash
docker compose up -d
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

## 저장소 구조

```text
db/init/                 DB 최초 생성 시 실행되는 초기화 SQL
docs/                    아키텍처와 포트폴리오 문서
docker-compose.yml       로컬/서버 재현 실행 정의
.env.example             공개용 환경변수 예시
```

추가 예정 구조:

```text
apps/ingest/             Markdown ingest 및 embedding pipeline
apps/api/                검색 및 관리 API
apps/mcp-server/         에이전트 접근용 MCP tools
db/migrations/           RAG schema migration
```
