from __future__ import annotations

import datetime as dt
from pathlib import Path


LOG_START = "=== [DANDI] :: Harness Helm (_start_) ==="
LOG_END = "=== [DANDI] :: Harness Helm (__end__) ==="


def now_kst() -> dt.datetime:
    return dt.datetime.now(dt.timezone(dt.timedelta(hours=9)))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def print_report(name: str, hard: list[str], warnings: list[str]) -> None:
    print(f"{name}: hard_errors={len(hard)} warnings={len(warnings)}")
    if hard:
        print("\n## Hard Errors")
        for item in hard:
            print(f"- {item}")
    if warnings:
        print("\n## Warnings")
        for item in warnings:
            print(f"- {item}")
