from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any


TOKEN_RE = re.compile(r"\w+|[^\s\w]", re.UNICODE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    content: str
    token_count: int
    content_hash: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class TextBlock:
    content: str
    token_count: int
    line_start: int
    line_end: int
    section_path: tuple[str, ...]
    heading: str | None


def count_tokens(text: str) -> int:
    return len(TOKEN_RE.findall(text))


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text)


def parse_markdown_blocks(text: str) -> list[TextBlock]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[TextBlock] = []
    section_stack: list[str] = []
    current: list[str] = []
    current_start = 1
    current_heading: str | None = None

    def flush(end_line: int) -> None:
        nonlocal current, current_start, current_heading
        content = "\n".join(current).strip()
        if content:
            blocks.append(
                TextBlock(
                    content=content,
                    token_count=count_tokens(content),
                    line_start=current_start,
                    line_end=end_line,
                    section_path=tuple(section_stack),
                    heading=current_heading,
                )
            )
        current = []
        current_heading = section_stack[-1] if section_stack else None

    for line_no, line in enumerate(lines, start=1):
        heading_match = HEADING_RE.match(line)
        if heading_match:
            flush(line_no - 1)
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            section_stack = section_stack[: level - 1]
            section_stack.append(title)
            blocks.append(
                TextBlock(
                    content=line.strip(),
                    token_count=count_tokens(line),
                    line_start=line_no,
                    line_end=line_no,
                    section_path=tuple(section_stack),
                    heading=title,
                )
            )
            current_start = line_no + 1
            current_heading = title
            continue

        if not line.strip():
            flush(line_no - 1)
            current_start = line_no + 1
            continue

        if not current:
            current_start = line_no
            current_heading = section_stack[-1] if section_stack else None
        current.append(line)

    flush(len(lines))
    return blocks


class MarkdownChunker:
    def __init__(self, chunk_size: int = 850, chunk_overlap: int = 120) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be zero or greater")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, text: str) -> list[TextChunk]:
        normalized = text.strip()
        if not normalized:
            return []

        blocks = parse_markdown_blocks(normalized)
        raw_chunks: list[tuple[str, dict[str, Any]]] = []
        current_parts: list[str] = []
        current_tokens = 0
        current_start: int | None = None
        current_end: int | None = None
        current_section: tuple[str, ...] = ()

        def emit_current() -> None:
            nonlocal current_parts, current_tokens, current_start, current_end, current_section
            content = "\n\n".join(part for part in current_parts if part.strip()).strip()
            if not content:
                return
            raw_chunks.append(
                (
                    content,
                    {
                        "section_path": list(current_section),
                        "heading": current_section[-1] if current_section else None,
                        "line_start": current_start,
                        "line_end": current_end,
                        "strategy": "markdown_heading_paragraph",
                    },
                )
            )
            current_parts = []
            current_tokens = 0
            current_start = None
            current_end = None
            current_section = ()

        for block in blocks:
            if block.token_count > self.chunk_size:
                emit_current()
                raw_chunks.extend(self._split_oversized_block(block))
                continue

            would_exceed = current_parts and current_tokens + block.token_count > self.chunk_size
            if would_exceed:
                emit_current()

            current_parts.append(block.content)
            current_tokens += block.token_count
            current_start = block.line_start if current_start is None else min(current_start, block.line_start)
            current_end = block.line_end if current_end is None else max(current_end, block.line_end)
            current_section = block.section_path or current_section

        emit_current()
        return [
            TextChunk(
                chunk_index=index,
                content=content,
                token_count=count_tokens(content),
                content_hash=hash_text(content),
                metadata=metadata,
            )
            for index, (content, metadata) in enumerate(raw_chunks)
        ]

    def _split_oversized_block(self, block: TextBlock) -> list[tuple[str, dict[str, Any]]]:
        tokens = split_tokens(block.content)
        chunks: list[tuple[str, dict[str, Any]]] = []
        start = 0
        split_index = 0
        step = self.chunk_size - self.chunk_overlap
        while start < len(tokens):
            end = min(start + self.chunk_size, len(tokens))
            content = " ".join(tokens[start:end]).strip()
            chunks.append(
                (
                    content,
                    {
                        "section_path": list(block.section_path),
                        "heading": block.heading,
                        "line_start": block.line_start,
                        "line_end": block.line_end,
                        "strategy": "hard_split",
                        "split_index": split_index,
                    },
                )
            )
            if end == len(tokens):
                break
            start += step
            split_index += 1
        return chunks
