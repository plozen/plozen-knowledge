# 이 파일은 Obsidian Vault 기본 위치를 고르는 공통 헬퍼를 제공한다.
from __future__ import annotations

from pathlib import Path


def default_vault_root() -> Path:
    # 서버별로 가능한 Obsidian Vault 위치를 순서대로 확인해 기본 경로를 고른다.
    candidates = [
        Path("/home/mhhan/ObsidianVault"),
        Path("/mnt/server13/mhhan/ObsidianVault"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]
