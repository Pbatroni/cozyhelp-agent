"""Clear local demo data (returns, sent emails, handoffs, feedback) before a demo.

Run:  python reset_demo.py
Only touches local files that are kept out of git. Sample orders and articles stay.
"""

from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

for name in ("returns.jsonl", "outbox.jsonl", "handoffs.jsonl", "feedback.jsonl"):
    path = DATA / name
    if path.exists():
        path.unlink()
        print(f"cleared {name}")

print("Demo data reset. The inbox is empty and returns can be requested again.")
