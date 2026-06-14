from __future__ import annotations

import json
import time
from typing import Any

from psycopg import sql
from psycopg.types.json import Jsonb

from .chunking import TextChunk, hash_text
from .database import Database
from .vector import uuid_array_literal, vector_literal


def merge_search_metadata(source_metadata: Any, chunk_metadata: Any) -> dict[str, Any]:
    source = source_metadata if isinstance(source_metadata, dict) else {}
    chunk = chunk_metadata if isinstance(chunk_metadata, dict) else {}
    return {
        **source,
        "chunk": chunk,
    }


class KnowledgeRepository:
    def __init__(self, database: Database) -> None:
        self.database = database

    def stage_source(
        self,
        *,
        source_type: str,
        source_uri: str,
        title: str,
        content: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        source_hash = hash_text(content)
        staged_metadata = {
            **metadata,
            "raw_content": content,
            "character_count": len(content),
            "content_hash": source_hash,
            "rag_status": "loaded",
        }
        with self.database.connection() as conn:
            existing = conn.execute(
                """
                SELECT id
                FROM document_sources
                WHERE source_uri = %s
                """,
                (source_uri,),
            ).fetchone()
            source_row = conn.execute(
                """
                INSERT INTO document_sources (source_type, source_uri, title, source_hash, metadata)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source_uri)
                DO UPDATE SET
                  source_type = EXCLUDED.source_type,
                  title = EXCLUDED.title,
                  source_hash = EXCLUDED.source_hash,
                  metadata = EXCLUDED.metadata,
                  updated_at = now()
                RETURNING id
                """,
                (source_type, source_uri, title, source_hash, Jsonb(staged_metadata)),
            ).fetchone()
            source_id = source_row["id"]
            conn.execute("DELETE FROM document_chunks WHERE source_id = %s", (source_id,))

        return {
            "source_id": str(source_id),
            "status": "loaded" if not existing else "updated",
            "chunk_count": 0,
            "source_hash": source_hash,
        }

    def get_source(self, source_id: str) -> dict[str, Any] | None:
        with self.database.connection() as conn:
            row = conn.execute(
                """
                SELECT
                  id,
                  source_type,
                  source_uri,
                  title,
                  source_hash,
                  metadata,
                  ingested_at,
                  updated_at
                FROM document_sources
                WHERE id = %s
                """,
                (source_id,),
            ).fetchone()
        return self._serialize_row(row) if row else None

    def get_unchanged_source(self, *, source_uri: str, source_hash: str) -> dict[str, Any] | None:
        with self.database.connection() as conn:
            existing = conn.execute(
                """
                SELECT id, source_hash
                FROM document_sources
                WHERE source_uri = %s
                """,
                (source_uri,),
            ).fetchone()
            if not existing or existing["source_hash"] != source_hash:
                return None

            chunk_count = conn.execute(
                "SELECT count(*) AS count FROM document_chunks WHERE source_id = %s",
                (existing["id"],),
            ).fetchone()["count"]

        return {
            "source_id": str(existing["id"]),
            "status": "skipped",
            "chunk_count": chunk_count,
            "source_hash": source_hash,
        }

    def upsert_source_chunks(
        self,
        *,
        source_type: str,
        source_uri: str,
        title: str,
        content: str,
        metadata: dict[str, Any],
        chunks: list[TextChunk],
        embeddings: list[list[float]],
    ) -> dict[str, Any]:
        source_hash = hash_text(content)
        with self.database.connection() as conn:
            existing = conn.execute(
                """
                SELECT id, source_hash
                FROM document_sources
                WHERE source_uri = %s
                """,
                (source_uri,),
            ).fetchone()

            source_row = conn.execute(
                """
                INSERT INTO document_sources (source_type, source_uri, title, source_hash, metadata)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source_uri)
                DO UPDATE SET
                  source_type = EXCLUDED.source_type,
                  title = EXCLUDED.title,
                  source_hash = EXCLUDED.source_hash,
                  metadata = EXCLUDED.metadata,
                  updated_at = now()
                RETURNING id
                """,
                (source_type, source_uri, title, source_hash, Jsonb(metadata)),
            ).fetchone()
            source_id = source_row["id"]

            conn.execute("DELETE FROM document_chunks WHERE source_id = %s", (source_id,))
            for chunk, embedding in zip(chunks, embeddings, strict=True):
                conn.execute(
                    """
                    INSERT INTO document_chunks (
                      source_id,
                      chunk_index,
                      content,
                      token_count,
                      embedding,
                      content_hash,
                      metadata
                    )
                    VALUES (%s, %s, %s, %s, %s::vector, %s, %s)
                    """,
                    (
                        source_id,
                        chunk.chunk_index,
                        chunk.content,
                        chunk.token_count,
                        vector_literal(embedding),
                        chunk.content_hash,
                        Jsonb(chunk.metadata),
                    ),
                )

            return {
                "source_id": str(source_id),
                "status": "created" if not existing else "updated",
                "chunk_count": len(chunks),
                "source_hash": source_hash,
            }

    def list_documents(self) -> list[dict[str, Any]]:
        with self.database.connection() as conn:
            rows = conn.execute(
                """
                SELECT
                  s.id,
                  s.source_type,
                  s.source_uri,
                  s.title,
                  s.source_hash,
                  s.metadata,
                  s.ingested_at,
                  s.updated_at,
                  count(c.id)::int AS chunk_count
                FROM document_sources s
                LEFT JOIN document_chunks c ON c.source_id = s.id
                GROUP BY s.id
                ORDER BY s.updated_at DESC
                """
            ).fetchall()
        return [self._serialize_row(row) for row in rows]

    def list_chunks(self, source_id: str) -> list[dict[str, Any]]:
        with self.database.connection() as conn:
            rows = conn.execute(
                """
                SELECT
                  id,
                  source_id,
                  chunk_index,
                  content,
                  token_count,
                  content_hash,
                  metadata,
                  created_at,
                  updated_at
                FROM document_chunks
                WHERE source_id = %s
                ORDER BY chunk_index ASC
                """,
                (source_id,),
            ).fetchall()
        return [self._serialize_row(row) for row in rows]

    def search(
        self,
        *,
        query_text: str,
        query_embedding: list[float],
        top_k: int,
        filters: dict[str, Any],
    ) -> dict[str, Any]:
        start = time.perf_counter()
        conditions = []
        query_vector = vector_literal(query_embedding)
        filter_params: list[Any] = []

        source_type = filters.get("source_type")
        if source_type:
            conditions.append(sql.SQL("s.source_type = %s"))
            filter_params.append(source_type)

        project = filters.get("project")
        if project:
            conditions.append(sql.SQL("s.metadata ->> 'project' = %s"))
            filter_params.append(project)

        where_clause = sql.SQL("")
        if conditions:
            where_clause = sql.SQL("WHERE ") + sql.SQL(" AND ").join(conditions)

        query = sql.SQL(
            """
            SELECT
              c.id AS chunk_id,
              c.source_id,
              s.source_type,
              s.source_uri,
              s.title,
              c.chunk_index,
              c.content,
              c.token_count,
              c.metadata AS chunk_metadata,
              s.metadata AS source_metadata,
              (c.embedding <=> %s::vector) AS distance
            FROM document_chunks c
            JOIN document_sources s ON s.id = c.source_id
            {where_clause}
            ORDER BY c.embedding <=> %s::vector
            LIMIT %s
            """
        ).format(where_clause=where_clause)

        # The query vector appears in SELECT and ORDER BY.
        query_params = [query_vector, *filter_params, query_vector, top_k]
        with self.database.connection() as conn:
            rows = conn.execute(query, query_params).fetchall()
            latency_ms = int((time.perf_counter() - start) * 1000)
            result_chunk_ids = [str(row["chunk_id"]) for row in rows]
            conn.execute(
                """
                INSERT INTO search_audit_logs (
                  query_text,
                  query_embedding,
                  tool_name,
                  top_k,
                  match_count,
                  filters,
                  latency_ms,
                  result_chunk_ids,
                  metadata
                )
                VALUES (%s, %s::vector, %s, %s, %s, %s, %s, %s::uuid[], %s)
                """,
                (
                    query_text,
                    vector_literal(query_embedding),
                    "api_search",
                    top_k,
                    len(rows),
                    Jsonb(filters),
                    latency_ms,
                    uuid_array_literal(result_chunk_ids),
                    Jsonb({"provider": "plozen-knowledge-api"}),
                ),
            )

        results = []
        for row in rows:
            item = self._serialize_row(row)
            chunk_metadata = item.pop("chunk_metadata") or {}
            source_metadata = item.pop("source_metadata") or {}
            item["metadata"] = merge_search_metadata(source_metadata, chunk_metadata)
            distance = float(item["distance"])
            item["distance"] = distance
            item["score"] = 1.0 - distance
            results.append(item)
        return {
            "query": query_text,
            "top_k": top_k,
            "match_count": len(results),
            "latency_ms": latency_ms,
            "results": results,
        }

    def list_audit_logs(self, limit: int = 20) -> list[dict[str, Any]]:
        with self.database.connection() as conn:
            rows = conn.execute(
                """
                SELECT
                  id,
                  query_text,
                  tool_name,
                  top_k,
                  match_count,
                  filters,
                  latency_ms,
                  result_chunk_ids,
                  metadata,
                  created_at
                FROM search_audit_logs
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
        return [self._serialize_row(row) for row in rows]

    def _serialize_row(self, row: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in row.items():
            if value is None:
                result[key] = None
            elif hasattr(value, "isoformat"):
                result[key] = value.isoformat()
            elif key == "metadata" or key == "filters":
                result[key] = self._json_value(value)
            elif key == "result_chunk_ids":
                result[key] = [str(item) for item in value]
            else:
                result[key] = str(value) if key.endswith("id") or key in {"id", "chunk_id", "source_id"} else value
        return result

    def _json_value(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            return json.loads(value)
        return dict(value)
