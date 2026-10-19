"""CozyHelp shopper chat. Run: python app.py, then open the link it prints.

This app is for shoppers only. It has no access to the support inbox, other
customers' data, or return approvals; those live in staff_app.py, behind a
password.
"""

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


with gr.Blocks(title="CozyHelp") as demo:
    gr.Markdown("# CozyHelp")
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


if __name__ == "__main__":
    demo.launch(inbrowser=True)
