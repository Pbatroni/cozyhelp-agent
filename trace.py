"""Capture a full CozyHelp trace: question, every tool call (arguments and
results), and the final response. Runs the raw agent with the code safeguards
OFF, so it shows what the model does on its own.

Run:  python trace.py "Your question here"
Saves each trace to traces/<timestamp>.json (kept out of git).
"""

import json
import sys
from datetime import datetime
from pathlib import Path

import agent

TRACES_DIR = Path(__file__).resolve().parent / "traces"


def _text(content: list) -> str:
    return " ".join(block["text"] for block in content if "text" in block).strip()


def capture(question: str) -> dict:
    agent._current_question = question
    bot = agent.build_agent()
    final = str(bot(question)).strip()

    tool_calls = {}
    order = []
    for message in bot.messages:
        for block in message.get("content", []):
            if "toolUse" in block:
                use = block["toolUse"]
                tool_calls[use["toolUseId"]] = {"tool": use["name"], "arguments": use["input"], "result": None}
                order.append(use["toolUseId"])
            if "toolResult" in block:
                result = block["toolResult"]
                if result["toolUseId"] in tool_calls:
                    tool_calls[result["toolUseId"]]["result"] = _text(result["content"])

    calls = [tool_calls[i] for i in order]
    return {
        "time": datetime.now().isoformat(timespec="seconds"),
        "model": "openrouter/openrouter/free",
        "safeguards": "off (raw agent)",
        "userInput": question,
        "toolCalls": calls,
        "handedOff": any(c["tool"] == "handoff_to_human" for c in calls),
        "finalResponse": final,
    }


if __name__ == "__main__":
    trace = capture(" ".join(sys.argv[1:]) or "What's your price match policy?")
    TRACES_DIR.mkdir(exist_ok=True)
    path = TRACES_DIR / f"{datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps(trace, indent=2) + "\n")
    print(json.dumps(trace, indent=2))
    print(f"\nSaved to {path}")
