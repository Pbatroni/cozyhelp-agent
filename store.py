"""Saves handoffs and helpful/not-helpful feedback to local files (kept out of git)."""

import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
HANDOFFS_FILE = DATA_DIR / "handoffs.jsonl"
FEEDBACK_FILE = DATA_DIR / "feedback.jsonl"


def _append(path: Path, record: dict) -> None:
    record = {"time": datetime.now().strftime("%Y-%m-%d %H:%M"), **record}
    with path.open("a") as f:
        f.write(json.dumps(record) + "\n")


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def save_handoff(question: str, summary: str, reason: str) -> None:
    _append(HANDOFFS_FILE, {"question": question, "summary": summary, "reason": reason})


def load_handoffs() -> list[dict]:
    """Newest first."""
    return list(reversed(_read(HANDOFFS_FILE)))


def save_feedback(question: str, answer: str, helpful: bool) -> None:
    _append(FEEDBACK_FILE, {"question": question, "answer": answer, "helpful": helpful})


def load_feedback() -> list[dict]:
    return list(reversed(_read(FEEDBACK_FILE)))
