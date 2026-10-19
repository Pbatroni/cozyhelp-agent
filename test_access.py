"""Tests for Valerie Zandoli's peer-testing findings. No AI model involved.

1. Shoppers can't reach the approval screen; only signed-in staff can approve.
2. If sending the label fails, the return stays pending and can be retried.
3. Two simultaneous approvals send exactly one label.

Run:  python test_access.py
"""

import inspect
import os
import sys
import tempfile
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import returns

tmp = Path(tempfile.mkdtemp())
returns.RETURNS_FILE = tmp / "returns.jsonl"
returns.OUTBOX_FILE = tmp / "outbox.jsonl"

results = []


def check(name, condition):
    results.append(condition)
    print(f"{'PASS' if condition else 'FAIL'}  {name}")


def fresh_request(item="Wool sweater"):
    returns.RETURNS_FILE.write_text("")
    returns.OUTBOX_FILE.write_text("")
    return returns.create_return_request("CC1001", "maya@example.com", item, "test")["request_id"]


# --- Finding 1: the shopper app has no way to approve ---------------------
import app  # noqa: E402

shopper_source = inspect.getsource(app)
check("shopper app doesn't import the returns module", "import returns" not in shopper_source)
check("shopper app has no approve or reject code", "approve_return" not in shopper_source and "reject_return" not in shopper_source)
buttons = [b for b in app.demo.blocks.values() if type(b).__name__ == "Button"]
check("shopper app has no Approve button", not any("Approve" in str(getattr(b, "value", "")) for b in buttons))

os.environ["STAFF_ACCOUNTS"] = "priscilla:correct-horse,joan:battery-staple"
import staff_app  # noqa: E402

check("staff login rejects a wrong password", not staff_app.check_login("priscilla", "guess"))
check("staff login rejects an unknown user", not staff_app.check_login("shopper", "correct-horse"))
check("staff login accepts the right password", staff_app.check_login("Priscilla", "correct-horse"))
os.environ["STAFF_ACCOUNTS"] = ""
check("staff login rejects everyone when no accounts are set", not staff_app.check_login("priscilla", "correct-horse"))

rid = fresh_request()
message = staff_app.decide(f"{rid} | x", True, SimpleNamespace(username=None))[0]
check("approving without being signed in is refused", "signed in" in message and len(returns.outbox()) == 0)
staff_app.decide(f"{rid} | x", True, SimpleNamespace(username="joan"))
reviewed_by = [r.get("reviewed_by") for r in returns.all_requests() if r["id"] == rid][0]
check("reviewer is the signed-in staff member, not typed text", reviewed_by == "joan")

# --- Finding 2: a failed send leaves the return retryable -----------------
rid = fresh_request()
real_send = returns._send_label


def broken_send(request):
    raise ConnectionError("email service down")


returns._send_label = broken_send
first = returns.approve_return(rid, "joan")
returns._send_label = real_send
status = [r["status"] for r in returns.all_requests() if r["id"] == rid][0]
check("failed send reports an error and leaves the return pending", not first["ok"] and status == "pending" and returns.outbox() == [])
retry = returns.approve_return(rid, "joan")
check("retry after a failed send works and sends exactly one label", retry["ok"] and len(returns.outbox()) == 1)

# --- Finding 3: simultaneous approvals send one label ---------------------
rid = fresh_request("Knit scarf")
real_read = returns._read


def read_slowly(path):
    data = real_read(path)
    time.sleep(0.2)  # widen the race window, like a slow disk
    return data


returns._read = read_slowly
threads = [threading.Thread(target=returns.approve_return, args=(rid, name)) for name in ("joan", "priscilla")]
[t.start() for t in threads]
[t.join() for t in threads]
returns._read = real_read
check("two simultaneous approvals send exactly one label", len(returns.outbox()) == 1)

request = [r for r in returns.all_requests() if r["id"] == rid][0]
returns._send_label(request)
check("sending the same request's label again does nothing", len(returns.outbox()) == 1)

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
