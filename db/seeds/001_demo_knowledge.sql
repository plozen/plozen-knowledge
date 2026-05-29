WITH sample_sources(source_type, source_uri, title, metadata) AS (
  VALUES
    ('obsidian_note', 'obsidian://07-History/2026-05-29/00-포트폴리오PDF배포-nexus.md', '2026-05-29 포트폴리오 PDF 배포 세션', '{"project":"portfolio","system":"history"}'::jsonb),
    ('project_doc', 'obsidian://02-Projects/plozen-knowledge/MOC-PLOZEN-Knowledge.md', 'PLOZEN Knowledge MOC', '{"project":"plozen-knowledge","system":"moc"}'::jsonb),
    ('todo_card', 'obsidian://01-Todo/Cards/2026-05-10-02-구직-플랫폼-가입-및-세팅.md', '구직 플랫폼 가입 및 세팅', '{"project":"career","system":"todo"}'::jsonb),
    ('architecture_doc', 'repo://docs/architecture.md', 'PLOZEN Knowledge Architecture', '{"project":"plozen-knowledge","system":"repo-doc"}'::jsonb)
),
upserted_sources AS (
  INSERT INTO document_sources (source_type, source_uri, title, source_hash, metadata)
  SELECT
    source_type,
    source_uri,
    title,
    encode(digest(source_uri || ':' || title, 'sha256'), 'hex'),
    metadata
  FROM sample_sources
  ON CONFLICT (source_uri) DO UPDATE SET
    source_type = EXCLUDED.source_type,
    title = EXCLUDED.title,
    source_hash = EXCLUDED.source_hash,
    metadata = EXCLUDED.metadata,
    updated_at = now()
  RETURNING id, source_uri
),
sample_chunks(source_uri, chunk_index, content, token_count, metadata, embedding_seed) AS (
  VALUES
    (
      'obsidian://07-History/2026-05-29/00-포트폴리오PDF배포-nexus.md',
      0,
      '제출용 포트폴리오 index.html을 블로그 기준으로 정리하고 PDF를 재생성했다. 검증 결과 7페이지, 텍스트 추출 정상, hyperlink 51개가 유지됐다.',
      47,
      '{"topic":"portfolio_pdf","evidence":"pdf"}'::jsonb,
      101
    ),
    (
      'obsidian://07-History/2026-05-29/00-포트폴리오PDF배포-nexus.md',
      1,
      'RAG 문제 정의는 검색 레이어 부족보다 전체 문맥을 매번 프롬프트에 붙이는 토큰 낭비와 근거 문서 수동 탐색 비용으로 정리했다.',
      42,
      '{"topic":"rag_problem","evidence":"copy"}'::jsonb,
      102
    ),
    (
      'obsidian://02-Projects/plozen-knowledge/MOC-PLOZEN-Knowledge.md',
      0,
      'PLOZEN Knowledge는 내부 문서, 프로젝트 기록, 세션 로그, 완료 Todo archive를 PostgreSQL pgvector 기반 RAG 저장소로 색인하고 MCP Server로 에이전트에게 제공한다.',
      52,
      '{"topic":"project_definition","layer":"core"}'::jsonb,
      201
    ),
    (
      'obsidian://02-Projects/plozen-knowledge/MOC-PLOZEN-Knowledge.md',
      1,
      'MVP 순서는 document_sources, document_chunks, search_audit_logs 스키마 생성 이후 Obsidian/Markdown ingest, embedding 저장, similarity search, MCP search_knowledge 연결이다.',
      45,
      '{"topic":"mvp_sequence","layer":"core"}'::jsonb,
      202
    ),
    (
      'obsidian://02-Projects/plozen-knowledge/MOC-PLOZEN-Knowledge.md',
      2,
      'Interface 계층은 FastAPI search/admin API와 MCP Server를 제공하고 search_knowledge, get_source, list_sources 도구를 노출한다.',
      38,
      '{"topic":"interface","layer":"api-mcp"}'::jsonb,
      203
    ),
    (
      'obsidian://02-Projects/plozen-knowledge/MOC-PLOZEN-Knowledge.md',
      3,
      'Agent Layer는 LangChain retriever, LangGraph workflow, Tool Calling, Agent Workflow를 통해 질문 분류, 검색, 답변, 감사로그 흐름으로 확장한다.',
      43,
      '{"topic":"agent_layer","layer":"agent"}'::jsonb,
      204
    ),
    (
      'obsidian://01-Todo/Cards/2026-05-10-02-구직-플랫폼-가입-및-세팅.md',
      0,
      '현재 본선은 지원서 제출보다 plozen-knowledge RAG/MCP 구현 증거를 먼저 만드는 것이다. pgvector, RAG, MCP Server를 핵심 키워드로 둔다.',
      44,
      '{"topic":"career_mainline","system":"todo"}'::jsonb,
      301
    ),
    (
      'repo://docs/architecture.md',
      0,
      'Obsidian과 Markdown 원문은 source of truth로 유지하고 RAG 데이터는 원문에서 파생된 검색 index로 관리한다.',
      33,
      '{"topic":"source_of_truth","system":"architecture"}'::jsonb,
      401
    ),
    (
      'repo://docs/architecture.md',
      1,
      'PostgreSQL은 관계형 metadata와 vector embedding을 함께 저장하고 pgvector는 SQL에서 cosine similarity search를 가능하게 한다.',
      35,
      '{"topic":"pgvector","system":"architecture"}'::jsonb,
      402
    ),
    (
      'repo://docs/architecture.md',
      2,
      '검색 감사 로그는 query_text, tool_name, top_k, match_count, result_chunk_ids를 저장해 포트폴리오 증거와 debugging 근거로 사용한다.',
      41,
      '{"topic":"audit_log","system":"architecture"}'::jsonb,
      403
    )
)
INSERT INTO document_chunks (
  source_id,
  chunk_index,
  content,
  token_count,
  embedding,
  content_hash,
  metadata
)
SELECT
  s.id,
  c.chunk_index,
  c.content,
  c.token_count,
  (
    SELECT array_agg(((mod(c.embedding_seed * 131 + gs.i * 17 + gs.i * c.embedding_seed, 997)::real) / 997.0) ORDER BY gs.i)::vector(1536)
    FROM generate_series(1, 1536) AS gs(i)
  ) AS embedding,
  encode(digest(c.content, 'sha256'), 'hex') AS content_hash,
  c.metadata
FROM sample_chunks c
JOIN upserted_sources s ON s.source_uri = c.source_uri
ON CONFLICT (source_id, chunk_index) DO UPDATE SET
  content = EXCLUDED.content,
  token_count = EXCLUDED.token_count,
  embedding = EXCLUDED.embedding,
  content_hash = EXCLUDED.content_hash,
  metadata = EXCLUDED.metadata,
  updated_at = now();
