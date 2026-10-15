"""Checkpoint tests for returns. No AI model involved.

Run:  python test_returns.py
Uses temporary files, so it never touches the real inbox.
"""

import sys
import tempfile
from pathlib import Path

import returns

tmp = Path(tempfile.mkdtemp())
returns.RETURNS_FILE = tmp / "returns.jsonl"
returns.OUTBOX_FILE = tmp / "outbox.jsonl"

results = []


def check(name, condition):
    results.append(condition)
    print(f"{'PASS' if condition else 'FAIL'}  {name}")


# Privacy: order number alone is not enough
check("wrong email can't see the order", returns.lookup_order("CC1001", "someone@else.com") is None)
r = returns.create_return_request("CC1001", "someone@else.com", "Wool sweater", "too small")
check("wrong email can't create a return", not r["ok"])

# Eligibility is decided in code
check("final sale item refused", not returns.create_return_request("CC1003", "sam@example.com", "Clearance boots", "changed mind")["ok"])
check("outside 30-day window refused", not returns.create_return_request("CC1002", "leo@example.com", "Rain jacket", "too big")["ok"])
check("not-yet-delivered order refused", not returns.create_return_request("CC1004", "ana@example.com", "Throw blanket", "don't want it")["ok"])
check("item not in the order refused", not returns.create_return_request("CC1001", "maya@example.com", "Laptop", "broken")["ok"])

# The checkpoint: creating a request sends nothing
r = returns.create_return_request("CC1001", "maya@example.com", "Wool sweater", "too small")
check("eligible return creates a request", r["ok"])
check("request is PENDING, not approved", returns.pending_requests()[0]["status"] == "pending")
check("no label email sent before approval", returns.outbox() == [])
check("duplicate request for same item refused", not returns.create_return_request("CC1001", "maya@example.com", "Wool sweater", "too small")["ok"])

# Reject sends nothing
r2 = returns.create_return_request("CC1001", "maya@example.com", "Knit scarf", "don't like the color")
returns.reject_return(r2["request_id"], "Joan")
check("rejected return sends no email", returns.outbox() == [])

# Approve sends exactly one email, once
returns.approve_return(r["request_id"], "Priscilla")
check("approval sends exactly one label email", len(returns.outbox()) == 1)
check("label goes to the order's email", returns.outbox()[0]["to"] == "maya@example.com")
again = returns.approve_return(r["request_id"], "Priscilla")
check("approving twice doesn't send a second email", not again["ok"] and len(returns.outbox()) == 1)

# Least privilege: the agent's view of an order hides the customer's email and prices
view = returns.public_view(returns.lookup_order("CC1001", "maya@example.com"))
check("order view hides the customer's email", "email" not in view)
check("order view keeps status and items", view["status"] == "delivered" and view["items"][0]["name"] == "Wool sweater")
check("order view hides item prices", "price" not in view["items"][0])

# Rate limit: max 3 return requests per customer per hour
returns.RETURNS_FILE.write_text("")
results_rl = [returns.create_return_request("CC1001", "maya@example.com", name, "test")["ok"] for name in ("Wool sweater", "Knit scarf")]
for r in returns.all_requests():
    returns.reject_return(r["id"], "test")
third = returns.create_return_request("CC1001", "maya@example.com", "Wool sweater", "again")
fourth = returns.create_return_request("CC1001", "maya@example.com", "Knit scarf", "again")
check("4th return request in an hour is blocked", all(results_rl) and third["ok"] and not fourth["ok"] and "Too many" in fourth["message"])

# The agent has no way to approve or send
import agent  # noqa: E402

agent_tools = set(agent.build_agent().tool_names)
check("agent has no approve or send tool", not ({"approve_return", "reject_return", "_send_label"} & agent_tools))

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
