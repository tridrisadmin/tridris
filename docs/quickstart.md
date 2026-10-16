# Quick start

From your access kit to your first approved action in about 10 minutes. You need the two things Tridris sent you:

- **Your agent token** (starts with `aat_`). Treat it like a password.
- **Your developer view link.** It also shows your API address under **Connect your agent**.

```bash
export TRIDRIS_URL="https://<the API address from your developer view>"
export TRIDRIS_AGENT_TOKEN="aat_..."
```

## 1. Find something to act on

Your agent works on a sample store with made-up customers and orders. List them:

```bash
curl -s "$TRIDRIS_URL/v1/demo/store" -H "Authorization: Bearer $TRIDRIS_AGENT_TOKEN"
```

Copy a customer `id`. The same list, with copy buttons, is at the bottom of your developer view. IDs change when we reset the demo, so list them again if one stops working.

## 2. Send three actions

New agents start with demo limits: store credit up to $250 runs on its own, $250 to $500 needs a person, and anything above $500 is blocked.

```bash
credit() {
  curl -s -X POST "$TRIDRIS_URL/v1/actions" \
    -H "Authorization: Bearer $TRIDRIS_AGENT_TOKEN" -H "Content-Type: application/json" \
    -d "{\"type\":\"store_credit\",\"params\":{\"customerId\":\"$CUSTOMER\",\"amountCents\":$1,\"reason\":\"Late delivery\"},\"run_id\":\"quickstart\",\"idempotency_key\":\"quickstart-$1-$(date +%s)\"}"
  echo
}
CUSTOMER="<customer id>"
credit 2500    # $25:  "status":"executed"
credit 30000   # $300: "status":"held", waiting for you
credit 90000   # $900: "status":"denied", above the maximum
```

Each answer has a `status`, the `reasons` as codes, and a plain-language `message` for your agent to pass on.

## 3. Approve the held one

Open your developer view. The $300 credit is under **Waiting for your approval**. Open it and click **Approve**. It runs, and the timeline shows who approved it and when.

Your agent can wait for the decision by polling `GET /v1/actions/<action_id>` until the status is no longer `held` (see the [TypeScript example](../examples/http/refund-tool.ts)).

## 4. Check the record

In the same action, click **Verify all** under **Records**. Each step (the decision, the approval, the result) has its own signed and sealed record, and all of them pass.

## 5. Change a limit

Under **Policy**, lower **Store credit → Needs approval above** to $10 and save. Send `credit 2500` again: it's now held. New requests use the new limits right away.

## 6. Connect your agent

Wrap the call in your agent's action tool: [an example agent on Claude, OpenAI, Gemini or Grok](../examples/agents/), a [Python or TypeScript tool](../examples/http/) or [n8n](../examples/n8n/README.md). Make sure the agent has no other way to reach your payment or store systems.

Then tell us how it went: [feedback](../../../issues/new/choose) or info@tridris.com.
