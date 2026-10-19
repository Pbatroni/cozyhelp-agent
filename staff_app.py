"""CozyHelp staff app: the Support team inbox. Password-protected and separate
from the shopper chat, so shoppers can't see other customers or approve returns.

Run:  python staff_app.py   (needs STAFF_ACCOUNTS in .env)
"""

import os
import sys

import gradio as gr
from dotenv import load_dotenv

import returns
import store

load_dotenv()

STAFF_PORT = 7861


def staff_accounts() -> dict[str, str]:
    """Read STAFF_ACCOUNTS from .env, formatted as "name:password,name:password"."""
    accounts = {}
    for pair in os.getenv("STAFF_ACCOUNTS", "").split(","):
        name, _, password = pair.strip().partition(":")
        if name and password:
            accounts[name.strip().lower()] = password.strip()
    return accounts


def check_login(username: str, password: str) -> bool:
    accounts = staff_accounts()
    return bool(accounts) and accounts.get(username.strip().lower()) == password


def inbox_view():
    handoffs = store.load_handoffs()
    feedback = store.load_feedback()
    rated = len(feedback)
    helpful = sum(1 for f in feedback if f["helpful"])
    rate = f"{helpful / rated:.0%}" if rated else "no ratings yet"
    stats = (
        f"**Handoffs waiting:** {len(handoffs)}  \n"
        f"**Helpful rate:** {rate} ({helpful} of {rated} rated answers)  \n"
        f"PRD target: at least 80% helpful"
    )
    handoff_rows = [[h["time"], h["question"], h["reason"], h["summary"]] for h in handoffs]
    feedback_rows = [[f["time"], "👍" if f["helpful"] else "👎", f["question"], f["answer"][:200]] for f in feedback]
    return stats, handoff_rows, feedback_rows


def returns_view():
    pending = returns.pending_requests()
    choices = [f"{r['id']} | {r['order_id']} | {r['item']} | ${r['price']:.2f}" for r in pending]
    rows = [[r["id"], r["status"], r["order_id"], r["email"], r["item"], f"${r['price']:.2f}",
             r["delivered_date"], r["eligibility"], r["shopper_reason"], r.get("reviewed_by", "")]
            for r in returns.all_requests()]
    sent = [[e["time"], e["to"], e["subject"]] for e in returns.outbox()]
    note = f"**Waiting for approval:** {len(pending)}"
    return note, gr.update(choices=choices, value=None), rows, sent


def decide(choice, approve, request: gr.Request):
    """The checkpoint: only a signed-in staff member can approve and send a label.
    The reviewer is whoever is signed in, not a name typed into a box."""
    reviewer = getattr(request, "username", None)
    if not reviewer:
        message = "You must be signed in as staff."
    elif not choice:
        message = "Pick a pending return first."
    else:
        request_id = choice.split(" | ")[0]
        action = returns.approve_return if approve else returns.reject_return
        message = action(request_id, reviewer)["message"]
    return (message, *returns_view())


def approve(choice, request: gr.Request):
    return decide(choice, True, request)


def reject(choice, request: gr.Request):
    return decide(choice, False, request)


def whoami(request: gr.Request):
    return f"Signed in as **{getattr(request, 'username', 'unknown')}**"


with gr.Blocks(title="CozyHelp Staff") as demo:
    gr.Markdown("# CozyHelp: Support team inbox")
    signed_in = gr.Markdown()
    demo.load(whoami, outputs=signed_in)

    refresh = gr.Button("Refresh")
    stats = gr.Markdown()
    gr.Markdown("### Handoffs")
    handoffs_table = gr.Dataframe(
        headers=["Time", "Shopper question", "Why", "Summary for the team"], wrap=True, interactive=False
    )
    gr.Markdown("### Feedback")
    feedback_table = gr.Dataframe(
        headers=["Time", "Rating", "Shopper question", "CozyHelp's answer"], wrap=True, interactive=False
    )
    outputs = [stats, handoffs_table, feedback_table]
    refresh.click(inbox_view, outputs=outputs)
    demo.load(inbox_view, outputs=outputs)

    gr.Markdown("### Return requests: human approval required")
    gr.Markdown("CozyHelp can only *create* a return request. The label email is sent only when a signed-in teammate approves it here.")
    returns_note = gr.Markdown()
    pending_pick = gr.Dropdown(label="Pending return", choices=[])
    with gr.Row():
        approve_btn = gr.Button("Approve and send label", variant="primary")
        reject_btn = gr.Button("Reject")
    decision_msg = gr.Markdown()
    returns_table = gr.Dataframe(
        headers=["Request", "Status", "Order", "Customer email", "Item", "Price", "Delivered", "Eligibility check", "Shopper's reason", "Reviewed by"],
        wrap=True, interactive=False,
    )
    gr.Markdown("### Sent emails (simulated outbox)")
    outbox_table = gr.Dataframe(headers=["Time", "To", "Subject"], wrap=True, interactive=False)

    returns_outputs = [returns_note, pending_pick, returns_table, outbox_table]
    approve_btn.click(approve, [pending_pick], [decision_msg, *returns_outputs])
    reject_btn.click(reject, [pending_pick], [decision_msg, *returns_outputs])
    refresh.click(returns_view, outputs=returns_outputs)
    demo.load(returns_view, outputs=returns_outputs)


if __name__ == "__main__":
    if not staff_accounts():
        sys.exit("Set STAFF_ACCOUNTS in .env (for example STAFF_ACCOUNTS=priscilla:a-long-password) before starting the staff app.")
    demo.launch(auth=check_login, auth_message="CozyHelp staff only. Sign in to see the support inbox.",
                server_port=STAFF_PORT, inbrowser=True)
