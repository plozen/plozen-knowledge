WITH query AS (
  SELECT
    'MCP search_knowledge에 연결할 RAG 스키마와 similarity search 증거는 무엇인가?'::text AS query_text,
    (
      SELECT array_agg(((mod(202 * 131 + gs.i * 17 + gs.i * 202, 997)::real) / 997.0) ORDER BY gs.i)::vector(1536)
      FROM generate_series(1, 1536) AS gs(i)
    ) AS embedding,
    5 AS top_k
),
matches AS (
  SELECT
    row_number() OVER (ORDER BY c.embedding <=> q.embedding) AS rank,
    c.id AS chunk_id,
    s.title AS source_title,
    s.source_uri,
    c.chunk_index,
    left(c.content, 160) AS preview,
    c.embedding <=> q.embedding AS cosine_distance
  FROM query q
  JOIN document_chunks c ON true
  JOIN document_sources s ON s.id = c.source_id
  ORDER BY c.embedding <=> q.embedding
  LIMIT (SELECT top_k FROM query)
),
audit AS (
  INSERT INTO search_audit_logs (
    query_text,
    query_embedding,
    tool_name,
    top_k,
    match_count,
    result_chunk_ids,
    metadata
  )
  SELECT
    q.query_text,
    q.embedding,
    'manual_sql_smoke',
    q.top_k,
    (SELECT count(*) FROM matches),
    ARRAY(SELECT chunk_id FROM matches ORDER BY rank),
    '{"smoke":"001_similarity_search"}'::jsonb
  FROM query q
  RETURNING id
)
SELECT
  audit.id AS audit_id,
  matches.rank,
  matches.source_title,
  matches.chunk_index,
  round(matches.cosine_distance::numeric, 6) AS cosine_distance,
  matches.preview
FROM audit
CROSS JOIN matches
ORDER BY matches.rank;
