"""CozyHelp chat app. Run: python app.py, then open the link it prints."""

import gradio as gr

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


demo = gr.ChatInterface(
    fn=respond,
    title="CozyHelp",
    description="Customer support for Cozy Cart, a fictional online store. Answers come only from help center articles; anything else goes to a human.",
    examples=[
        "How do I return a sweater I bought last week?",
        "How long does shipping take?",
        "I forgot my password",
        "What's your policy on returning gift card items bought during a flash sale?",
    ],
)

if __name__ == "__main__":
    demo.launch(inbrowser=True)
