# CozyHelp

An AI customer support agent for Cozy Cart, a fictional online store, that answers shoppers' questions about orders, returns, and accounts using only trusted help center articles, and hands off to a human when it isn't sure.

**Owners:** Priscilla and Joan

## Setup

1. Copy `.env.example` to `.env` and add your own keys.
2. Never commit `.env` — it's blocked by `.gitignore`.

## Run the chat app

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Tests

- `python test_search.py` checks the help center search (no AI model).
- `python test_returns.py` checks the return checkpoint (no AI model).
- `python test_evals.py 3` runs the PRD Eval Card against the real agent, 3 times each.

## Start a return (with human approval)

Shoppers can start a return by giving their order number, the email on the order, the item, and a reason. CozyHelp checks the order and eligibility in code (30-day window, not final sale, delivered), then creates a **pending** return request.

**Checkpoint:** the return label email is irreversible, so it's only sent when a support teammate clicks **Approve** in the Support team inbox. The agent has no tool to approve or send, so no prompt or shopper message can get it past the checkpoint. `python test_returns.py` tests this.

Sample orders for testing are in `data/orders.json` (for example `CC1001` / `maya@example.com`).

## Safety design

- Answers only from help center articles and cites the source.
- Code safeguards hand off to a human when a message mentions a specific order or a damaged/missing item, or when the agent's reply has no cited source.
