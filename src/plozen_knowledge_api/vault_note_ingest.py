# 이 파일은 선택한 Obsidian Markdown 노트를 Knowledge API용 문서 객체로 변환한다.
# VaultNoteDocument는 노트 1개의 내용, source URI, 제목, metadata를 들고 있는 데이터 클래스다.
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable


@dataclass(frozen=True)
class VaultNoteDocument:
    path: Path
    relative_path: str
    filename: str
    title: str
    content: str
    project: str
    domain: str
    knowledge_type: str
    visibility: str = "internal"

    @property
    def source_uri(self) -> str:
        # Knowledge API에서 원본 위치를 구분할 때 쓰는 Obsidian URI를 만든다.
        return f"obsidian://{self.relative_path}"

    @property
    def source_title(self) -> str:
        # 검색 결과와 문서 목록에 표시할 노트 제목을 반환한다.
        return self.title

    @property
    def metadata(self) -> dict[str, object]:
        # 도메인 지식 검색 필터에 필요한 프로젝트, 분류, 파일 경로 정보를 구성한다.
        return {
            "project": self.project,
            "domain": self.domain,
            "source": "obsidian",
            "vault_path": self.relative_path,
            "knowledge_type": self.knowledge_type,
            "visibility": self.visibility,
            "filename": self.filename,
            "character_count": len(self.content),
        }


def normalize_vault_note_path(relative_path: str) -> str:
    # CLI에서 받은 경로가 vault 안의 Markdown 상대경로인지 검증하고 정규화한다.
    raw_path = relative_path.replace("\\", "/").strip()
    path = PurePosixPath(raw_path)
    if not raw_path or path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Vault note path must be a relative path inside the vault: {relative_path}")
    if path.suffix.lower() != ".md":
        raise ValueError(f"Vault note path must point to a Markdown file: {relative_path}")
    return path.as_posix()


def infer_note_title(relative_path: str, content: str) -> str:
    # 첫 번째 H1 제목이 있으면 제목으로 쓰고, 없으면 파일명을 제목으로 쓴다.
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            heading = stripped.removeprefix("# ").strip()
            if heading:
                return heading
    return PurePosixPath(relative_path).stem


def load_vault_note_document(
    vault_root: Path,
    relative_path: str,
    *,
    project: str,
    domain: str,
    knowledge_type: str,
    visibility: str = "internal",
) -> VaultNoteDocument:
    # 실제 파일 내용을 읽고 Knowledge API에 보낼 VaultNoteDocument로 변환한다.
    normalized_path = normalize_vault_note_path(relative_path)
    path = vault_root / normalized_path
    if not path.exists():
        raise FileNotFoundError(f"Vault note not found: {path}")
    if not path.is_file():
        raise ValueError(f"Vault note path is not a file: {path}")

    content = path.read_text(encoding="utf-8")
    return VaultNoteDocument(
        path=path,
        relative_path=normalized_path,
        filename=path.name,
        title=infer_note_title(normalized_path, content),
        content=content,
        project=project,
        domain=domain,
        knowledge_type=knowledge_type,
        visibility=visibility,
    )


def collect_vault_note_documents(
    vault_root: Path,
    paths: Iterable[str],
    *,
    project: str,
    domain: str,
    knowledge_type: str,
    visibility: str = "internal",
) -> list[VaultNoteDocument]:
    # 선택된 여러 vault 노트를 입력 순서대로 문서 객체 목록으로 만든다.
    return [
        load_vault_note_document(
            vault_root,
            path,
            project=project,
            domain=domain,
            knowledge_type=knowledge_type,
            visibility=visibility,
        )
        for path in paths
    ]
