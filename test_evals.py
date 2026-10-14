"""Eval Card from the PRD (section 3d). Runs the real agent, checks tool calls.

Run:  python test_evals.py            (each case once)
      python test_evals.py 5          (each case 5 times)
"""

import sys

from agent import answer

CASES = [
    {
        "name": "1 - Golden (normal)",
        "question": "How do I return a sweater I bought last week?",
        "must_call": ["get_article"],
        "must_not_call": ["handoff_to_human"],
        "reply_must_include": ["Source"],
    },
    {
        "name": "2 - Golden (edge: damaged order + refund)",
        "question": "My order #CC1042 arrived damaged and I want my money back.",
        "must_call": ["handoff_to_human"],
        "must_not_call": [],
        "reply_must_include": [],
    },
    {
        "name": "3 - Adversarial (no article answers it)",
        "question": "What's your policy on returning gift card items bought during a flash sale?",
        "must_call": ["handoff_to_human"],
        "must_not_call": [],
        "reply_must_include": [],
    },
]


def run_case(case) -> tuple[bool, str]:
    result = answer(case["question"])
    reply = result["reply"]
    used = result["tools"]
    problems = []
    for name in case["must_call"]:
        if name not in used:
            problems.append(f"did not call {name}")
    for name in case["must_not_call"]:
        if name in used:
            problems.append(f"should not call {name}")
    for text in case["reply_must_include"]:
        if text.lower() not in reply.lower():
            problems.append(f"reply missing '{text}'")
    return not problems, f"({result['why']}) tools={used} " + ("; ".join(problems) if problems else "")


if __name__ == "__main__":
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    failures = 0
    for case in CASES:
        for i in range(runs):
            ok, detail = run_case(case)
            failures += not ok
            print(f"{'PASS' if ok else 'FAIL'}  {case['name']} (run {i + 1})  {detail}")
    print(f"\nFailures: {failures}/{len(CASES) * runs}")
    sys.exit(1 if failures else 0)
