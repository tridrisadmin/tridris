# Integration guide

Your agent sends each action to Tridris before it happens. Tridris checks it against the limits you set for that agent, then runs it, holds it for a person, or blocks it, and seals a verifiable record either way. One HTTPS call per action; no change to how your agent reasons.

## How it fits

Pick how much Tridris does. You can move from one mode to the next without changing your agent's code.

| Mode | What you connect | Who carries out the action |
|---|---|---|
| **Watch** | Read-only access to your store and payments | Nobody: Tridris replays your last 30 days against your limits and reports what it would have held or blocked |
| **Decision-only** | Nothing that moves money | Your own system, after Tridris returns a signed authorization |
| **Enforce** | Store and payment credentials, kept only in Tridris | Tridris, so your agent never holds those credentials |

On the hosted demo your agent runs in Enforce mode against a sample store. Design partners choose the mode that suits them.

## 1. Setup

| You get | What it is | Keep it |
|---|---|---|
| API address | Your Tridris instance (shown in your developer view) | In config |
| Agent token | One per agent; it identifies the agent and its limits | In your secret store, never in prompts, logs or client-side code |
| Developer view link | Your agent's actions, approvals, limits and records | Private: anyone with it can approve your agent's actions |

Give your agent one tool per action (for example `issue_refund`) whose code calls Tridris instead of your payment or store API. The model never sees the token. Plain HTTPS and JSON work from any language: `Authorization: Bearer <agent token>`.

## 2. Request an action

One call: `POST /v1/actions`. Money is always integer cents.

```bash
curl -X POST "$TRIDRIS_URL/v1/actions" \
  -H "Authorization: Bearer $TRIDRIS_AGENT_TOKEN" -H 'Content-Type: application/json' \
  -d '{"type":"refund","params":{"orderId":"<order ID>","amountCents":190000,"reason":"Wrong size"},"run_id":"conv_88","idempotency_key":"refund-T4471"}'
```

What comes back, and what your agent should tell the customer:

| `status` | Meaning | What your agent does |
|---|---|---|
| `executed` | Within limits and done | Confirm it; `target_ref` holds the store or payment ID |
| `held` | Waiting for a person to approve | Say it is waiting for approval; never say it is done |
| `denied` | Outside the limits | Explain `message` in plain words and offer an alternative |
| `approved` | Cleared, Decision-only | Your system carries it out (section 3) |
| `failed` | The store or payment system did not complete it | Say so; nothing changed |

Every response also carries `action_id`, `decision`, `reasons`, a plain-language `message` and `receipt_ids`. Full details: [API reference](api-reference.md).

### Works with any agent

Tridris works with any model, framework or agent builder that lets you define a tool and make an authenticated HTTPS call. The tool's code calls Tridris, and the model only sees the result. See the [example agents](../examples/agents/) on Claude, OpenAI, Gemini and Grok, plain [Python and TypeScript tools](../examples/http/), and [n8n](../examples/n8n/README.md). Builders such as Copilot Studio or Agentforce connect the same way, through their custom connector or HTTP action. If a builder can't keep the token secret from the model or its users, put a small service of your own between them that holds the token.

No ready-made plugins exist yet (no MCP server or marketplace connector). Whatever you use, make sure the agent has no other route to your payment or store API.

## 3. Held actions and Decision-only

**Held actions.** A held action waits for an approver, who decides in the dashboard or from a link on their phone (optionally with a passkey). On the demo, that's you, in your developer view. Your agent can poll `GET /v1/actions/{action_id}` until the status changes ([TypeScript example](../examples/http/refund-tool.ts)). Approvals expire after the window you set (24 hours by default). Rejected and expired actions change nothing, and any money reserved for them is released.

**Decision-only.** Tridris decides and records, and your own system carries out the action with its own credentials:

1. A cleared action comes back as `approved` with an `authorization` (`token` and `expires_at`).
2. Your executor checks the token before acting: its Ed25519 signature against the keys at `GET /.well-known/aar-keys.json`, its expiry, and that it names this action, type and parameters. A token for $150 cannot pay $1,500. Tridris gives pilot partners a ready-made check.
3. Your system runs the action, then reports with `POST /v1/actions/{action_id}/result`. Report `failed` if it did not run.
4. Tridris seals the result and checks your store, read-only, that it really happened.

## 4. Errors and retries

**Retries are safe.** Send the same `idempotency_key` with the same request and you get the first result back (HTTP 200 instead of 201). Nothing runs twice.

**Tridris fails closed.** If a check, the database or the sealing service is unavailable, the action does not run and you get `503 system_unavailable`. Your agent should say it will try again shortly, never that the action happened.

## 5. Records and security

**Records.** Every decision, approval and result, blocked attempts included, is signed by Tridris and countersigned by a separate sealing service. Each record is chained to the one before it, so edits and deletions show. Check them in your developer view with **Verify**; design partners can also export evidence packages.

**Security.**
- Treat the agent token like a password. If it leaks, ask us to turn it off; it only ever works within that agent's limits.
- Never put card numbers, bank details or passwords in `params` or `reason`. Tridris never stores card or bank details.
- In Decision-only mode, Tridris holds no credentials that move money. In Enforce mode, your store and payment credentials stay inside Tridris and are never given to the agent.

**Before you go live:**
- [ ] Limits and approvers set for each agent
- [ ] Each action tool calls Tridris, and nothing else can reach your payment or store API from the agent
- [ ] `held`, `denied` and `503` handled, with the agent wording each one honestly
- [ ] Idempotency keys derived from your ticket or task ID, reused on retries
- [ ] Decision-only: your executor checks every authorization and reports every result
- [ ] A test run in Observe mode, which records what would have been held or blocked without blocking anything

Questions or a new action type: info@tridris.com.
