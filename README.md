# CozyHelp

An AI customer support agent for **Cozy Cart**, a fictional online store. CozyHelp answers shoppers' questions using only trusted help center articles, shows its source, starts eligible returns, and hands the conversation to a person whenever it isn't sure.

**Owners:** Priscilla Batroni and Joan Albayrak

## What it does

- **Answers policy questions** (returns, refunds, shipping, pre-orders, gift cards, promo codes, accounts) from 10 sample help center articles, and ends each answer with its source.
- **Looks up an order**, but only when the shopper gives both the order number and the email on the order.
- **Starts a return**: checks eligibility in code (delivered, within 30 days, not final sale) and creates a *pending* return request.
- **Hands off to a human** when no article answers the question, when an item is damaged or missing, or when the shopper is upset. Every handoff lands in the Support team inbox with a summary.
- **Support team inbox**: a second page where staff see handoffs, 👍/👎 ratings, and pending returns, and **approve or reject** each return.

## Role and industry

- **Industry:** online retail (e-commerce)
- **Function:** customer support
- **Who it serves:** shoppers with quick questions, and the support team, who receive clean handoffs and approve returns

## How to run it

Requires **Python 3.10 or newer** and a free [OpenRouter](https://openrouter.ai) API key. Check with `python3 --version`; the Python that comes with macOS is often 3.9, which is too old. If yours is older, install 3.12 from [python.org](https://www.python.org/downloads/) or with [uv](https://docs.astral.sh/uv/) (`uv python install 3.12`).

```bash
git clone https://github.com/Pbatroni/cozyhelp-agent.git
cd cozyhelp-agent
python3 -m venv .venv                                      # must be Python 3.10+
source .venv/bin/activate
pip install --only-binary cryptography -r requirements.txt
cp .env.example .env        # then put your own OPENROUTER_API_KEY in .env
python app.py               # opens the chat app in your browser
```

`--only-binary cryptography` makes pip use a prebuilt version of the `cryptography` package. Without it, the install fails on Intel Macs, which have no prebuilt version of the newest release.

Try it with the sample orders in `data/orders.json`, for example:
> *I want to return the Wool sweater from order CC1001, my email is maya@example.com. It's too small.*

Then open the **Support team inbox** tab to approve or reject the return.

Note: the free OpenRouter tier allows about 50 AI requests a day, and each question uses several.

### Tests

| Command | What it checks | Uses AI? |
|---|---|---|
| `python test_search.py` | Help center search finds the right article | No |
| `python test_returns.py` | Return checkpoint, privacy check, rate limit, order field limits | No |
| `python test_safeguards.py` | False "approved/sent" claims, internal note stripping, tool allowlist | No |
| `python test_evals.py 3` | The PRD Eval Card against the real agent, 3 runs each | Yes |
| `python trace.py "question"` | Saves a full trace (tool calls, arguments, results) with safeguards off | Yes |

## Safety design

- **Human approval for the irreversible step.** The agent can only *create* a return request. The return label email is sent only when a support teammate clicks **Approve** in the inbox. The agent has no tool to approve or send.
- **Deny-by-default tool allowlist.** The agent only gets the tools listed in `TOOL_PERMISSIONS` in `agent.py`; anything not listed is denied.
- **Least privilege.** Order lookups require the order number *and* email, and return only the fields the agent needs (no customer email or prices). Return requests are limited to 3 per customer per hour.
- **Code safeguards, not just prompt rules.** We found in real traces that the free model sometimes *said* it was handing off without calling the tool. The harness now:
  - hands off when a reply says "connecting you" without a handoff, or gives a policy answer with no cited source;
  - replaces any false claim that a return was approved or a label was sent or re-sent;
  - removes internal handoff notes before the shopper sees the reply;
  - hands off immediately for damaged or missing items.
- **Graceful failure.** If the AI service fails, shoppers see a friendly message, never a raw error.
- **Secrets stay local.** `.env`, handoffs, feedback, returns and traces are all excluded from git.

## Out of scope

- **No real store, customers or payments.** Cozy Cart, its articles and its orders are fictional sample data.
- **No real emails.** Approved return labels go to a local simulated outbox.
- **No refunds, exchanges or policy exceptions.** CozyHelp never decides these; it hands off to a person.
- **No accounts, sign-in or pre-ordering.** CozyHelp answers questions about these but can't perform them.
- **No live help center integration.** Our design targets Front's Knowledge Base API; this version uses local sample articles with keyword search.
- **No memory between messages.** Each message is answered on its own.
