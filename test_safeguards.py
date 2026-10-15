"""Tests for the code safeguards and tool allowlist. No AI model involved.

Run:  python test_safeguards.py
"""

import sys

import agent

results = []


def check(name, condition):
    results.append(condition)
    print(f"{'PASS' if condition else 'FAIL'}  {name}")


# False claims are caught, honest wording is not
claims = [
    ("Your return has been approved!", True),
    ("I've approved your return.", True),
    ("I sent you the return label.", True),
    ("Your label was sent.", True),
    ("I've re-sent your label.", True),
    ("I resent the label to your email.", True),
    ("Done, I sent a new label.", True),
    ("You'll get a label once it's approved.", False),
    ("It will be emailed until it is approved by a teammate.", False),
    ("It's waiting to be approved by a teammate.", False),
    ("Here is the present you asked about.", False),
]
for text, should_flag in claims:
    check(f"claim check {'flags' if should_flag else 'allows'}: {text!r}", bool(agent.FALSE_APPROVAL.search(text)) == should_flag)

# Internal handoff notes never reach the shopper
leaky = "I'm connecting you with our team.\n\n**Hand-off summary for support:** The shopper asked about gift cards."
check("internal handoff summary is removed", agent.strip_internal_notes(leaky) == "I'm connecting you with our team.")
check("normal reply is unchanged", agent.strip_internal_notes("Standard shipping takes 5-7 days.") == "Standard shipping takes 5-7 days.")

# Deny-by-default allowlist
tools = set(agent.build_agent().tool_names)
check("agent has exactly the allowlisted tools", tools == set(agent.TOOL_PERMISSIONS))
agent.TOOL_PERMISSIONS.pop("request_return")
check("removing a tool from the allowlist removes it from the agent", "request_return" not in agent.build_agent().tool_names)

print(f"\n{sum(results)}/{len(results)} passed")
sys.exit(0 if all(results) else 1)
