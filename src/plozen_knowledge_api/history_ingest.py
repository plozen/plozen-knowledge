# 이 파일은 Obsidian 07-History 세션 노트를 읽어서 HistoryDocument로 변환한다.
# HistoryDocument는 세션 노트 1개의 내용, source URI, 제목, metadata를 들고 있는 데이터 클래스다.
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
from typing import Iterator

from .vault_paths import default_vault_root


DATE_DIR_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HISTORY_FILENAME_PATTERN = re.compile(
    r"^(?P<order>\d{2})-(?P<title>.+)-(?P<agent>arche|nexus|sentinel|pulse|mason|hermes|openclaw|unknown)\.md$"
)


@dataclass(frozen=True)
class HistoryDocument:
    path: Path
    relative_path: str
    session_date: date
    filename: str
    title: str
    content: str
    order: int | None = None
    agent: str = "unknown"

    @property
    def source_uri(self) -> str:
        # Knowledge API에서 원본 위치를 구분할 때 쓰는 Obsidian URI를 만든다.
        return f"obsidian://{self.relative_path}"

    @property
    def source_title(self) -> str:
        # 검색 결과와 문서 목록에 표시할 날짜 포함 제목을 만든다.
        return f"{self.session_date.isoformat()} {self.title}"

    @property
    def metadata(self) -> dict[str, object]:
        # History 전용 검색 필터에 필요한 날짜, agent, 파일 경로 정보를 구성한다.
        return {
            "project": "PLOZEN",
            "domain": "session-history",
            "source": "obsidian",
            "vault_path": self.relative_path,
            "session_date": self.session_date.isoformat(),
            "filename": self.filename,
            "character_count": len(self.content),
            "agent": self.agent,
            "order": self.order,
        }


def parse_date(value: str | None) -> date | None:
    # CLI 옵션 문자열을 date 객체로 바꾸고, 값이 없으면 필터를 비운다.
    if not value:
        return None
    return date.fromisoformat(value)


def iter_history_files(
    vault_root: Path,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> Iterator[Path]:
    # 07-History 날짜 폴더를 순회하면서 조건에 맞는 Markdown 파일 경로를 반환한다.
    history_root = vault_root / "07-History"
    if not history_root.exists():
        raise FileNotFoundError(f"History directory not found: {history_root}")

    dated_dirs: list[tuple[date, Path]] = []
    for child in history_root.iterdir():
        if not child.is_dir() or not DATE_DIR_PATTERN.match(child.name):
            continue
        session_date = date.fromisoformat(child.name)
        if date_from and session_date < date_from:
            continue
        if date_to and session_date > date_to:
            continue
        dated_dirs.append((session_date, child))

    for _, session_dir in sorted(dated_dirs, key=lambda item: item[0]):
        files = [path for path in session_dir.iterdir() if path.is_file() and path.suffix == ".md"]
        yield from sorted(files, key=history_file_sort_key)


def history_file_sort_key(path: Path) -> tuple[int, str]:
    # 같은 날짜 안에서 00, 01 같은 세션 번호가 먼저 오도록 정렬 키를 만든다.
    parsed = parse_history_filename(path.name)
    order = parsed[0] if parsed else 999
    return (order, path.name)


def parse_history_filename(filename: str) -> tuple[int, str, str] | None:
    # NN-제목-agent.md 형식의 History 파일명에서 순번, 제목, agent를 추출한다.
    match = HISTORY_FILENAME_PATTERN.match(filename)
    if not match:
        return None
    return int(match.group("order")), match.group("title"), match.group("agent")


def load_history_document(vault_root: Path, path: Path) -> HistoryDocument:
    # 실제 파일 내용을 읽고 Knowledge API에 보낼 HistoryDocument로 변환한다.
    relative_path = path.relative_to(vault_root).as_posix()
    session_date = date.fromisoformat(path.parent.name)
    parsed = parse_history_filename(path.name)
    if parsed:
        order, title, agent = parsed
    else:
        order, title, agent = None, path.stem, "unknown"
    return HistoryDocument(
        path=path,
        relative_path=relative_path,
        session_date=session_date,
        filename=path.name,
        title=title,
        content=path.read_text(encoding="utf-8"),
        order=order,
        agent=agent,
    )


def collect_history_documents(
    vault_root: Path,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
    agent: str | None = None,
    limit: int | None = None,
) -> list[HistoryDocument]:
    # 날짜, agent, 개수 제한을 적용해 ingest 대상 HistoryDocument 목록을 만든다.
    documents: list[HistoryDocument] = []
    for path in iter_history_files(vault_root, date_from=date_from, date_to=date_to):
        document = load_history_document(vault_root, path)
        if agent and document.agent != agent:
            continue
        documents.append(document)
        if limit is not None and len(documents) >= limit:
            break
    return documents
