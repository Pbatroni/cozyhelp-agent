"""CozyHelp chat app. Run: python app.py, then open the link it prints."""

import gradio as gr

import returns
import store
from agent import answer


def respond(message, history):
    try:
        result = answer(message)
    except Exception as error:
        # Graceful failure: never show a raw error to a shopper.
        print(f"[ERROR] {type(error).__name__}: {error}")
        return (
            "Sorry, CozyHelp is having trouble right now. "
            "Please try again in a little while, or contact our support team directly."
        )
    reply = result["reply"]
    if result["handed_off"]:
        reply += "\n\n*(Handed off to the Cozy Cart support team.)*"
    return reply


def _text(content) -> str:
    """Chat message content can be a string or a list of parts."""
    if isinstance(content, list):
        return " ".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
    return str(content)


def on_feedback(data: gr.LikeData, history):
    """Save a thumbs up / down on one of CozyHelp's answers."""
    index = data.index[0] if isinstance(data.index, (list, tuple)) else data.index
    answer_text = _text(data.value)
    question = ""
    for message in reversed(history[:index]):
        if message.get("role") == "user":
            question = _text(message.get("content", ""))
            break
    store.save_feedback(question, answer_text, helpful=bool(data.liked))


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


def decide(choice, reviewer, approve):
    """The checkpoint: only a person clicking here can approve and send a label."""
    if not choice:
        message = "Pick a pending return first."
    elif not reviewer.strip():
        message = "Enter your name as the reviewer."
    else:
        request_id = choice.split(" | ")[0]
        action = returns.approve_return if approve else returns.reject_return
        message = action(request_id, reviewer.strip())["message"]
    return (message, *returns_view())


with gr.Blocks(title="CozyHelp") as demo:
    gr.Markdown("# CozyHelp")
    with gr.Tab("Shopper chat"):
        gr.Markdown(
            "Customer support for Cozy Cart, a fictional online store. Answers come only from "
            "help center articles; anything else goes to a human. Use 👍 / 👎 to rate an answer."
        )
        chatbot = gr.Chatbot(height=460)
        gr.ChatInterface(
            fn=respond,
            chatbot=chatbot,
            examples=[
                "How do I return a sweater I bought last week?",
                "I want to return the Wool sweater from order CC1001, my email is maya@example.com. It's too small.",
                "Can I pre-order the winter jacket?",
                "My promo code isn't working",
                "What's your policy on returning gift card items bought during a flash sale?",
            ],
        )
        chatbot.like(on_feedback, inputs=[chatbot])

    with gr.Tab("Support team inbox") as inbox_tab:
        gr.Markdown("Conversations CozyHelp handed off, and how shoppers rated its answers.")
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
        inbox_tab.select(inbox_view, outputs=outputs)
        demo.load(inbox_view, outputs=outputs)

        gr.Markdown("### Return requests: human approval required")
        gr.Markdown("CozyHelp can only *create* a return request. The label email is sent only when a teammate approves it here.")
        returns_note = gr.Markdown()
        pending_pick = gr.Dropdown(label="Pending return", choices=[])
        reviewer = gr.Textbox(label="Your name (reviewer)")
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
        approve_btn.click(lambda c, r: decide(c, r, True), [pending_pick, reviewer], [decision_msg, *returns_outputs])
        reject_btn.click(lambda c, r: decide(c, r, False), [pending_pick, reviewer], [decision_msg, *returns_outputs])
        refresh.click(returns_view, outputs=returns_outputs)
        inbox_tab.select(returns_view, outputs=returns_outputs)
        demo.load(returns_view, outputs=returns_outputs)

if __name__ == "__main__":
    demo.launch(inbrowser=True)
