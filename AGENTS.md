# PLOZEN Knowledge Agent Rules

## Identity

This repository is the PLOZEN Knowledge RAG backend. It provides PostgreSQL/pgvector storage, FastAPI search/admin APIs, and the MCP server layer for agent-facing knowledge retrieval.

## Runtime Boundary

- Primary runtime is Server-13.
- Server-13 local path: `/mnt/data/workspace/plozen-knowledge`
- Nexus-11 mounted path: `/mnt/server13/mhhan/workspace/plozen-knowledge`
- GitHub remote: `https://github.com/plozen/plozen-knowledge.git`

## Public Boundary

- Keep this repository public-safe by default.
- Do not commit `.env`, API keys, OpenAI keys, database passwords, raw private Obsidian vault content, customer secrets, or internal Discord tokens.
- `.env.example` may include variable names and safe placeholders only.
- Demo seeds and smoke evidence must use public-safe sample text.

## Product Direction

Current MVP order:

1. PostgreSQL + pgvector RAG schema.
2. Markdown/text ingest, chunking, and embeddings.
3. FastAPI document/search/admin endpoints.
4. MCP tools: `search_knowledge`, `get_source`, `list_sources`.
5. Search/tool audit logs for portfolio evidence.
6. LangChain/LangGraph and GraphRAG are later expansion layers, not MVP blockers.

## Implementation Rules

- Keep the FastAPI API and MCP tool layer separate.
- MCP tools should call the API/client layer instead of duplicating database logic.
- Search results should include source, chunk, score, metadata, and audit/log identifiers when available.
- Upload/stage and vectorize flows may be separate so the Ops Console can show `loaded` vs `vector` states.
- Do not change the database schema without adding or updating migration SQL and tests.

## Verification

Before commit or push:

- `git diff --check`
- `pytest`
- API smoke test when API behavior changes
- Secret scan if `gitleaks` or another scanner is available locally

If local Python dependencies are missing, report that explicitly instead of treating tests as passed.
