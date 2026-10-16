# Tridris

**Check · Trace · Seal for AI agent actions.**

Tridris sits between your AI agents and the systems they act on, wherever the agents are built. Routine actions run straight away, risky ones wait for a person to approve, and anything outside your limits is blocked. Every action, including blocked ones, ends in a signed, verifiable record.

| | |
|---|---|
| **Check**, before it runs | Limits you set for each agent: what it may do, how much, how often, and when a person must approve. |
| **Trace**, while it runs | Every action is tied to the agent, the task it came from and the person who approved it. |
| **Seal**, once it's done | A record signed by Tridris, countersigned by a separate sealing service and chained to the one before, so edits and deletions show. |

## Try it with your own agent

We're inviting developers and teams who build AI agents to try Tridris on our hosted demo and tell us what works and what doesn't. It's free, and no real money moves.

1. **[Request access](https://tridris.com/partner-with-us/)**, or email **info@tridris.com** with your name, company and what your agents do.
2. **Get your access kit:** an agent token for your agent and a private link to your developer view.
3. **Connect your agent** with the [quick start](docs/quickstart.md). It takes about 10 minutes and one HTTPS call per action.

**[Request access →](https://tridris.com/partner-with-us/)**

### What you get

- **Your own agent** with its own limits, on a sample store: refunds, store credit, cancellations, address and email changes, discount codes.
- **A private developer view** ([what's in it](docs/developer-view.md)): your agent's actions as they happen, held actions for you to approve or reject (optionally with a passkey on your phone), limits you can change, and verified records.
- **These docs and examples**, ready to copy into your agent.

## Works with how you build agents

Your agent's action tools call one HTTPS endpoint instead of your payment or store API. The model never sees the token. That works with agents built on any model (for example Claude, Grok, OpenAI GPT or Gemini), with frameworks and SDKs (for example LangChain, CrewAI, the OpenAI Agents SDK or the Claude Agent SDK), with agent builders such as n8n, or with your own code.

```bash
curl -X POST "$TRIDRIS_URL/v1/actions" \
  -H "Authorization: Bearer $TRIDRIS_AGENT_TOKEN" -H "Content-Type: application/json" \
  -d '{"type":"store_credit","params":{"customerId":"<customer ID>","amountCents":2500,"reason":"Late delivery"},"run_id":"ticket-4471","idempotency_key":"credit-4471"}'
```

The answer says what happened and why: `executed`, `held` (waiting for a person) or `denied`, with a plain-language `message` your agent can pass on.

## Documentation

| | |
|---|---|
| [Quick start](docs/quickstart.md) | From token to your first approved action |
| [Integration guide](docs/integration-guide.md) | Modes, requests, held actions, Decision-only, retries, security, launch checklist |
| [API reference](docs/api-reference.md) | Endpoints, fields, statuses, reason codes and errors |
| [Developer view](docs/developer-view.md) | What your private link shows and what you can do there |

## Examples

| Example | Status |
|---|---|
| [Example agents on Claude, OpenAI, Gemini and Grok](examples/agents/) | Tools and loops tested against Tridris; Claude is how our own demo agent runs |
| [Python tool](examples/http/refund_tool.py), standard library only | Tested |
| [TypeScript tool](examples/http/refund-tool.ts), with waiting for a decision | Tested |
| [curl](examples/http/actions.sh): the three outcomes | Tested |
| [n8n HTTP Request node](examples/n8n/README.md) | Example, not yet tested by us |

Each example reads `TRIDRIS_URL` and `TRIDRIS_AGENT_TOKEN` from the environment. Keep the token in your secret store, never in prompts, logs or client-side code.

## Feedback

Already trying Tridris? Tell us what worked, what didn't and what's missing: [open a feedback issue](../../issues/new/choose) or email **info@tridris.com**. Please never post tokens, links or personal data in public issues.

Need an action type we don't have yet (payouts, access grants, deployments …)? [Request it](../../issues/new/choose).

## About

- Tridris is a hosted service. This repository holds documentation and example integration code only, not the Tridris software.
- Hosted on SOC 2 Type II infrastructure. Tridris never stores card or bank details.
- Records use Ed25519 signatures (RFC 8032), canonical JSON (RFC 8785) and SHA-256, in AAR (Agent Action Receipt), an open record format designed by Tridris. Specification on request.
- © Tridris. All rights reserved. The example code may be used only to connect your agents to Tridris; see the [license](LICENSE).

*Names are used to describe where agents are built. Tridris is not affiliated with or endorsed by these companies.*

[tridris.com](https://tridris.com) · info@tridris.com
