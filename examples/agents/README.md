# Example agents: Claude, OpenAI, Gemini and Grok

The same small customer-support agent on four model providers. Each one uses the shared [`tridris_tools.py`](tridris_tools.py), so every action it takes (refund, store credit, cancellation, discount code) goes through Tridris first, and you watch the decisions in your developer view.

| File | Provider | SDK | What we've checked |
|---|---|---|---|
| [`claude_agent.py`](claude_agent.py) | Anthropic Claude | `anthropic` | Tools and loop tested against Tridris; our own demo agent runs on Claude |
| [`openai_agent.py`](openai_agent.py) | OpenAI | `openai` | Tools and loop tested against Tridris with simulated model replies; not yet run with a live OpenAI model by us |
| [`gemini_agent.py`](gemini_agent.py) | Google Gemini | `google-genai` | Same as OpenAI |
| [`grok_agent.py`](grok_agent.py) | xAI Grok | `openai` (xAI's OpenAI-compatible API) | Same as OpenAI |

## Run one

```bash
cd examples/agents
python -m venv .venv && . .venv/bin/activate
pip install anthropic            # or: openai, google-genai

export TRIDRIS_URL="https://<the API address from your developer view>"
export TRIDRIS_AGENT_TOKEN="aat_..."
# Or, for an organization: let the agent register itself with your Connect key (Tridris -> Settings)
# and leave TRIDRIS_AGENT_TOKEN unset. It appears in Tridris -> Agents as Needs review.
# export TRIDRIS_CONNECT_KEY="tck_..."  TRIDRIS_AGENT_NAME="Claude support agent"

export ANTHROPIC_API_KEY=...                         # Claude
# export OPENAI_API_KEY=... OPENAI_MODEL=...         # OpenAI
# export GEMINI_API_KEY=... GEMINI_MODEL=...         # Gemini
# export XAI_API_KEY=... XAI_MODEL=...               # Grok

python claude_agent.py
```

For OpenAI, Gemini and Grok, set the model to a current model from that provider that supports function or tool calling.

## Things to try

Ask as a customer would. The agent calls `list_orders` to find the order, then asks Tridris:

- "My order #1002 arrived late. Can I get a $20 credit?" → runs straight away.
- "I want a $300 credit for the trouble." → **waits for approval**. Approve it in your developer view, then ask "Has my credit been approved?"
- "Give me $900 in credit." → **blocked**, with the reason.
- "Cancel order #1001." → depends on the order's value and whether it shipped.
- Ask for the same thing four times for one customer → the per-customer daily limit stops it.

Then lower a limit in your developer view and ask again: the decision changes, without touching the agent's code.

## Using it in your own agent

Copy `tridris_tools.py` and register its `TOOLS` with your agent, or wrap your existing action tools so they call `POST /v1/actions` instead of your payment or store API. Make sure the agent has no other way to reach those systems.
