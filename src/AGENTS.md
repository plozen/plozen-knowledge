# PLOZEN Knowledge Source Rules

## Package Layout

- `plozen_knowledge_api/`: FastAPI backend, database access, chunking, embeddings, and RAG search services.
- `plozen_knowledge_mcp/`: MCP server package for agent-facing tools.

## Boundaries

- Do not put MCP tool definitions inside `plozen_knowledge_api/`.
- Do not duplicate database queries in the MCP package.
- MCP tools should call a small API client layer that talks to the FastAPI service.
- Shared behavior belongs in explicit shared modules only when both API and MCP need it.

## MCP Tool Direction

Initial MCP tools:

- `search_knowledge`: query the Knowledge API search endpoint.
- `list_sources`: list document sources from the Knowledge API.
- `get_source`: fetch one source and its chunks or metadata.

Tool responses should stay compact and include source, chunk, score, metadata, and audit/log identifiers when available.
