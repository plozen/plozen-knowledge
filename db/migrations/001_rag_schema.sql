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

COMMENT ON TABLE document_sources IS 'RAG 색인 대상 원본 문서. Obsidian note, 프로젝트 문서, Todo archive, 업로드 파일 같은 source 단위를 저장한다.';
COMMENT ON COLUMN document_sources.id IS '원본 문서의 내부 UUID primary key.';
COMMENT ON COLUMN document_sources.source_type IS '원본 유형. 예: obsidian_note, project_doc, todo_card, uploaded_file, architecture_doc.';
COMMENT ON COLUMN document_sources.source_uri IS '원본 문서를 다시 찾기 위한 고유 URI 또는 경로. 예: obsidian://..., repo://..., upload://...';
COMMENT ON COLUMN document_sources.title IS '검색 결과와 관리자 UI에 표시할 원본 문서 제목.';
COMMENT ON COLUMN document_sources.source_hash IS '원본 내용 또는 식별값 기준 hash. 변경 감지와 중복 ingest 방지에 사용한다.';
COMMENT ON COLUMN document_sources.metadata IS '프로젝트명, 태그, 작성자, 파일 형식 같은 원본 문서 메타데이터 JSON.';
COMMENT ON COLUMN document_sources.ingested_at IS '이 source가 RAG 저장소에 처음 들어온 시각.';
COMMENT ON COLUMN document_sources.updated_at IS 'source metadata 또는 hash가 마지막으로 갱신된 시각.';

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

COMMENT ON TABLE document_chunks IS '검색 가능한 문서 조각. 원본 문서를 chunking한 텍스트와 embedding vector를 저장한다.';
COMMENT ON COLUMN document_chunks.id IS '문서 조각의 내부 UUID primary key.';
COMMENT ON COLUMN document_chunks.source_id IS '이 chunk가 속한 원본 문서 document_sources.id.';
COMMENT ON COLUMN document_chunks.chunk_index IS '원본 문서 안에서의 chunk 순서. source_id와 함께 중복을 방지한다.';
COMMENT ON COLUMN document_chunks.content IS '검색 결과로 반환하고 LLM context에 주입할 chunk 본문.';
COMMENT ON COLUMN document_chunks.token_count IS 'chunk 본문 기준 예상 token 수. context budget 관리에 사용한다.';
COMMENT ON COLUMN document_chunks.embedding IS 'chunk 본문을 embedding한 pgvector 값. 현재 차원은 1536.';
COMMENT ON COLUMN document_chunks.content_hash IS 'chunk 본문 hash. 중복 chunk 감지와 재색인 판단에 사용한다.';
COMMENT ON COLUMN document_chunks.metadata IS 'heading, section, page, line range, tags 같은 chunk 단위 메타데이터 JSON.';
COMMENT ON COLUMN document_chunks.created_at IS 'chunk가 처음 생성된 시각.';
COMMENT ON COLUMN document_chunks.updated_at IS 'chunk content, embedding, metadata가 마지막으로 갱신된 시각.';

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

COMMENT ON TABLE search_audit_logs IS '검색 실행 감사 로그. API, MCP, 수동 SQL smoke test의 query와 결과 chunk ID를 기록한다.';
COMMENT ON COLUMN search_audit_logs.id IS '검색 로그의 내부 UUID primary key.';
COMMENT ON COLUMN search_audit_logs.query_text IS '사용자 또는 에이전트가 요청한 원문 검색 질의.';
COMMENT ON COLUMN search_audit_logs.query_embedding IS '검색 질의를 embedding한 vector. 재현/debugging이 필요할 때 사용한다.';
COMMENT ON COLUMN search_audit_logs.tool_name IS '검색을 실행한 도구 또는 엔드포인트 이름. 예: manual_sql_smoke, api_search, search_knowledge.';
COMMENT ON COLUMN search_audit_logs.top_k IS '검색 요청에서 요구한 최대 결과 개수.';
COMMENT ON COLUMN search_audit_logs.match_count IS '실제로 반환된 검색 결과 개수.';
COMMENT ON COLUMN search_audit_logs.filters IS 'source_type, project, date range 같은 검색 필터 JSON.';
COMMENT ON COLUMN search_audit_logs.latency_ms IS '검색 처리 시간(ms). API/MCP 구현 후 성능 관측에 사용한다.';
COMMENT ON COLUMN search_audit_logs.result_chunk_ids IS '검색 결과로 반환된 document_chunks.id 배열. 순서는 rank 순서를 따른다.';
COMMENT ON COLUMN search_audit_logs.metadata IS '호출자, model, session_id, smoke test 이름 같은 추가 실행 메타데이터 JSON.';
COMMENT ON COLUMN search_audit_logs.created_at IS '검색이 실행된 시각.';

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
