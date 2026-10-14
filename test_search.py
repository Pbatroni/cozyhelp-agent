"""Match / no-match test for search_help_center. No AI model involved.

Run:  python test_search.py
Add --sweep to see how different MIN_SCORE values perform.
"""

import sys

import help_center
from help_center import search_help_center

# Questions that SHOULD find an article -> the article the top result must be
SHOULD_MATCH = [
    ("How do I return a sweater I bought last week?", "returns-policy"),
    ("Can I send this back?", "returns-policy"),
    ("Can I exchange shoes for a different size?", "returns-policy"),
    ("When will I get my money back?", "refunds"),
    ("How long does a refund take?", "refunds"),
    ("How long does shipping take?", "shipping-delivery"),
    ("Do you ship to Canada?", "shipping-delivery"),
    ("Where is my order?", "order-status"),
    ("How do I track my package?", "order-status"),
    ("I forgot my password", "account-password"),
    ("How do I change the email on my account?", "account-password"),
    ("My order arrived damaged", "damaged-missing"),
    ("Can I pre-order the winter jacket?", "pre-orders"),
    ("How do I check my gift card balance?", "gift-cards"),
    ("My promo code isn't working", "promo-codes"),
    ("How do I cancel my order?", "order-changes"),
]

# Off-topic questions that should find NOTHING
SHOULD_NOT_MATCH = [
    "What's the weather today?",
    "Do you sell cars?",
    "Tell me a joke",
    "Who won the game last night?",
    "What is the capital of France?",
    # Harder: share words with real articles but aren't support questions
    "Can I order a pizza?",
    "What account do you use on Instagram?",
    "Is your delivery driver single?",
]


def run() -> tuple[int, int]:
    misses = 0
    false_matches = 0
    for question, expected in SHOULD_MATCH:
        results = search_help_center(question)
        top = results[0]["id"] if results else None
        ok = top == expected
        misses += not ok
        print(f"{'PASS' if ok else 'MISS'}  {question!r} -> {top} (expected {expected})")
    for question in SHOULD_NOT_MATCH:
        results = search_help_center(question)
        ok = not results
        false_matches += not ok
        found = [r["id"] for r in results]
        print(f"{'PASS' if ok else 'FALSE MATCH'}  {question!r} -> {found or 'nothing'}")
    return misses, false_matches


if __name__ == "__main__":
    if "--sweep" in sys.argv:
        import contextlib, io
        for threshold in range(1, 9):
            help_center.MIN_SCORE = threshold
            with contextlib.redirect_stdout(io.StringIO()):
                misses, false_matches = run()
            print(f"MIN_SCORE={threshold}: misses={misses}, false matches={false_matches}")
    else:
        misses, false_matches = run()
        print(f"\nMisses: {misses}/{len(SHOULD_MATCH)}   False matches: {false_matches}/{len(SHOULD_NOT_MATCH)}")
        # Misses fail the test. False matches are allowed at this layer:
        # the agent reads the article and hands off if it doesn't answer.
        sys.exit(1 if misses else 0)
