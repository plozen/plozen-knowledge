# 이 파일은 선택한 Obsidian 노트를 dry-run 하거나 Knowledge API에 ingest하는 터미널 명령을 제공한다.
# --path로 받은 Markdown 노트를 읽고 Knowledge API의 /documents/ingest 엔드포인트로 보낸다.
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from plozen_knowledge_mcp.client import KnowledgeApiClient

from .config import load_dotenv
from .vault_note_ingest import collect_vault_note_documents
from .vault_paths import default_vault_root


def build_parser() -> argparse.ArgumentParser:
    # vault note ingest CLI에서 받을 경로, metadata, dry-run 옵션을 정의한다.
    load_dotenv()
    parser = argparse.ArgumentParser(description="Ingest selected Obsidian Markdown notes into PLOZEN Knowledge.")
    parser.add_argument("--vault-root", type=Path, default=default_vault_root(), help="Obsidian vault root path.")
    parser.add_argument(
        "--api-base-url",
        default=os.getenv("KNOWLEDGE_API_BASE_URL", "http://127.0.0.1:3200"),
        help="PLOZEN Knowledge API base URL.",
    )
    parser.add_argument("--api-key", default=os.getenv("KNOWLEDGE_API_KEY"), help="Knowledge API key.")
    parser.add_argument("--path", dest="paths", action="append", required=True, help="Vault-relative Markdown path.")
    parser.add_argument("--project", required=True, help="Project filter value stored in metadata.")
    parser.add_argument("--domain", default="project-knowledge", help="Domain filter value stored in metadata.")
    parser.add_argument("--knowledge-type", default="project-doc", help="Knowledge type stored in metadata.")
    parser.add_argument("--visibility", default="internal", help="Visibility value stored in metadata.")
    parser.add_argument("--source-type", default="project_doc", help="Knowledge API source_type value.")
    parser.add_argument("--dry-run", action="store_true", help="List planned documents without API writes.")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on the first ingest error.")
    return parser


def summarize_document(document: Any) -> dict[str, Any]:
    # dry-run 출력용으로 문서의 핵심 metadata와 문자 수만 요약한다.
    return {
        "source_uri": document.source_uri,
        "title": document.source_title,
        "metadata": document.metadata,
        "characters": len(document.content),
    }


def main() -> int:
    # CLI 진입점으로, dry-run이면 목록만 출력하고 아니면 Knowledge API에 ingest한다.
    args = build_parser().parse_args()
    documents = collect_vault_note_documents(
        args.vault_root,
        args.paths,
        project=args.project,
        domain=args.domain,
        knowledge_type=args.knowledge_type,
        visibility=args.visibility,
    )

    if args.dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "count": len(documents),
                    "documents": [summarize_document(document) for document in documents],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    client = KnowledgeApiClient(base_url=args.api_base_url, api_key=args.api_key)
    results: list[dict[str, Any]] = []
    try:
        for document in documents:
            try:
                result = client.ingest_document(
                    source_type=args.source_type,
                    source_uri=document.source_uri,
                    title=document.source_title,
                    content=document.content,
                    metadata=document.metadata,
                )
            except Exception as exc:  # noqa: BLE001 - CLI should report per-document failures.
                result = {
                    "source_uri": document.source_uri,
                    "title": document.source_title,
                    "status": "error",
                    "error": str(exc),
                }
                if args.fail_fast:
                    raise
            results.append(result)
            print(json.dumps(result, ensure_ascii=False))
    finally:
        client.close()

    created = sum(1 for item in results if item.get("status") == "created")
    updated = sum(1 for item in results if item.get("status") == "updated")
    skipped = sum(1 for item in results if item.get("status") == "skipped")
    errors = sum(1 for item in results if item.get("status") == "error")
    print(
        json.dumps(
            {
                "processed": len(results),
                "created": created,
                "updated": updated,
                "skipped": skipped,
                "errors": errors,
            },
            ensure_ascii=False,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
