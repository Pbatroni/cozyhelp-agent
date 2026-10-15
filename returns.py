"""Orders and return requests, with a human-in-the-loop checkpoint.

The agent can look up an order and CREATE a return request. It cannot
approve one or send a label: those functions are only called from the
Support team inbox, by a person. That's the checkpoint, and it lives in
code, so no prompt or shopper message can talk the agent past it.
"""

import json
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
ORDERS_FILE = DATA_DIR / "orders.json"
RETURNS_FILE = DATA_DIR / "returns.jsonl"
OUTBOX_FILE = DATA_DIR / "outbox.jsonl"

RETURN_WINDOW_DAYS = 30

# Least privilege: the agent only ever sees these order fields (never the customer's email).
ALLOWED_ORDER_FIELDS = {"order_id", "status", "delivered_date", "tracking_number", "items"}
ALLOWED_ITEM_FIELDS = {"name", "final_sale"}

# Rate limit: at most this many return requests per customer email per hour.
RETURN_LIMIT_PER_HOUR = 3


def _orders() -> list[dict]:
    return json.loads(ORDERS_FILE.read_text())


def lookup_order(order_id: str, email: str) -> dict | None:
    """Return the order only if BOTH the order number and email match (privacy check)."""
    order_id = order_id.strip().upper().lstrip("#")
    email = email.strip().lower()
    for order in _orders():
        if order["order_id"] == order_id and order["email"].lower() == email:
            return order
    return None


def public_view(order: dict) -> dict:
    """Only the fields the agent needs to answer order questions."""
    view = {k: v for k, v in order.items() if k in ALLOWED_ORDER_FIELDS}
    view["items"] = [{k: v for k, v in i.items() if k in ALLOWED_ITEM_FIELDS} for i in order["items"]]
    return view


def check_eligibility(order: dict, item_name: str, today: date | None = None) -> tuple[bool, str, dict | None]:
    """Decide in code whether an item can be returned. Returns (eligible, reason, item)."""
    today = today or date.today()
    item = next((i for i in order["items"] if i["name"].lower() == item_name.strip().lower()), None)
    if item is None:
        names = ", ".join(i["name"] for i in order["items"])
        return False, f"That item isn't in this order. Items: {names}.", None
    if order["status"] != "delivered" or not order.get("delivered_date"):
        return False, "The order hasn't been delivered yet.", item
    if item["final_sale"]:
        return False, "Final sale items can't be returned.", item
    days = (today - date.fromisoformat(order["delivered_date"])).days
    if days > RETURN_WINDOW_DAYS:
        return False, f"It was delivered {days} days ago; the return window is {RETURN_WINDOW_DAYS} days.", item
    return True, f"Delivered {days} days ago, within the {RETURN_WINDOW_DAYS}-day window; not final sale.", item


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _write(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(r) + "\n" for r in records))


def create_return_request(order_id: str, email: str, item_name: str, reason: str) -> dict:
    """Agent-facing: verify, then save a PENDING request. Never sends anything."""
    order = lookup_order(order_id, email)
    if order is None:
        return {"ok": False, "message": "No order matches that order number and email."}
    eligible, why, item = check_eligibility(order, item_name)
    if not eligible:
        return {"ok": False, "message": why}

    requests = _read(RETURNS_FILE)
    hour_ago = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M")
    recent = [r for r in requests if r["email"] == order["email"] and r["created"] >= hour_ago]
    if len(recent) >= RETURN_LIMIT_PER_HOUR:
        return {"ok": False, "message": "Too many return requests in the last hour. Please try again later or contact support."}
    for r in requests:
        if r["order_id"] == order["order_id"] and r["item"] == item["name"] and r["status"] in ("pending", "approved"):
            return {"ok": False, "message": f"A return for this item already exists ({r['id']}, {r['status']})."}

    request = {
        "id": f"R-{uuid.uuid4().hex[:6].upper()}",
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "order_id": order["order_id"],
        "email": order["email"],
        "item": item["name"],
        "price": item["price"],
        "delivered_date": order["delivered_date"],
        "eligibility": why,
        "shopper_reason": reason,
        "status": "pending",
    }
    _write(RETURNS_FILE, requests + [request])
    return {"ok": True, "request_id": request["id"], "message": "Return request created and waiting for a support teammate to approve it."}


def pending_requests() -> list[dict]:
    return [r for r in _read(RETURNS_FILE) if r["status"] == "pending"]


def all_requests() -> list[dict]:
    return list(reversed(_read(RETURNS_FILE)))


def _decide(request_id: str, approve: bool, reviewer: str) -> dict:
    requests = _read(RETURNS_FILE)
    for r in requests:
        if r["id"] == request_id:
            if r["status"] != "pending":
                return {"ok": False, "message": f"{request_id} is already {r['status']}."}
            r["status"] = "approved" if approve else "rejected"
            r["reviewed_by"] = reviewer
            r["reviewed"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            _write(RETURNS_FILE, requests)
            if approve:
                _send_label(r)
            return {"ok": True, "message": f"{request_id} {r['status']}."}
    return {"ok": False, "message": f"No request {request_id}."}


def approve_return(request_id: str, reviewer: str) -> dict:
    """HUMAN ONLY (Support inbox). Approves and sends the label."""
    return _decide(request_id, True, reviewer)


def reject_return(request_id: str, reviewer: str) -> dict:
    """HUMAN ONLY (Support inbox)."""
    return _decide(request_id, False, reviewer)


def _send_label(request: dict) -> None:
    """The irreversible step. Simulated: writes to a local outbox instead of real email."""
    email = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "to": request["email"],
        "subject": f"Your Cozy Cart return label ({request['id']})",
        "body": f"Your return for {request['item']} from order {request['order_id']} is approved. Your prepaid label is attached.",
    }
    with OUTBOX_FILE.open("a") as f:
        f.write(json.dumps(email) + "\n")


def outbox() -> list[dict]:
    return list(reversed(_read(OUTBOX_FILE)))
