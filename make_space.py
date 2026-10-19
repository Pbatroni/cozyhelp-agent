"""Build a clean bundle of the PUBLIC CozyHelp (shopper chat only) for Hugging Face Spaces.

Run:  python make_space.py
Creates space_build/ (kept out of git). It never includes .env, the staff app,
passwords, or any local shopper data. Add OPENROUTER_API_KEY as a Space secret.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "space_build"

FILES = ["app.py", "agent.py", "help_center.py", "returns.py", "store.py", "requirements.txt"]
DATA = ["articles.json", "orders.json"]

HEADER = """---
title: CozyHelp
emoji: 🛒
colorFrom: orange
colorTo: yellow
sdk: gradio
sdk_version: 6.30.0
app_file: app.py
pinned: false
license: mit
short_description: AI support agent for a fictional online store
---

"""

NOTE = """
## About this demo

This is the public shopper chat for **CozyHelp**, an AI customer support agent for a
fictional online store (Cozy Cart). It answers only from help center articles, cites its
source, and hands off to a person when it isn't sure. It runs on a free model, so if it
says it's having trouble, the daily free limit may be used up. Try again later.

Return requests created here wait for staff approval in a separate, password-protected
staff app that is not part of this public demo, so no label is ever sent from this page.

Code: https://github.com/Pbatroni/cozyhelp-agent
"""

if OUT.exists():
    shutil.rmtree(OUT)
(OUT / "data").mkdir(parents=True)

for name in FILES:
    shutil.copy(ROOT / name, OUT / name)
for name in DATA:
    shutil.copy(ROOT / "data" / name, OUT / "data" / name)

(OUT / "README.md").write_text(HEADER + NOTE)

# Safety check: nothing secret or staff-only in the bundle
leaks = [p.name for p in OUT.rglob("*") if p.name in {".env", "staff_app.py"} or p.suffix in {".jsonl", ".lock"}]
assert not leaks, f"bundle contains files it should not: {leaks}"
print("Built", OUT, "with:", sorted(str(p.relative_to(OUT)) for p in OUT.rglob("*") if p.is_file()))
