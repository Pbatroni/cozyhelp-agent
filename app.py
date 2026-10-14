"""CozyHelp chat app. Run: python app.py, then open the link it prints."""

import gradio as gr

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

if __name__ == "__main__":
    demo.launch(inbrowser=True)
