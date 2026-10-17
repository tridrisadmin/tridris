# API reference

Base address: the API address shown in your developer view (your Tridris instance). Every request needs your agent token:

```
Authorization: Bearer aat_...
```

Money is always integer cents. Requests and responses are JSON.

## Endpoints

| Method and path | What it does |
|---|---|
| `POST /v1/actions` | Ask to take an action. Returns the decision, and the result if it ran. |
| `GET /v1/actions/{action_id}` | The current state of one of your agent's actions, for example after it was held. |
| `POST /v1/actions/{action_id}/result` | Decision-only mode: report what your system did with an authorized action. |
| `GET /v1/demo/store` | Demo only: the sample customers and orders your agent can act on. |
| `GET /.well-known/aar-keys.json` | The public keys that sign records and authorizations. No token needed. |

## POST /v1/actions

```json
{
  "type": "refund",
  "params": { "orderId": "…", "amountCents": 190000, "reason": "Wrong size" },
  "signals": { "newDevice": false, "locationMismatch": false, "verifiedIdentity": true },
  "run_id": "conv_88",
  "idempotency_key": "refund-T4471"
}
```

| Field | Required | Notes |
|---|---|---|
| `type` | Yes | One of the action types below |
| `params` | Yes | Depends on the type; every type needs a `reason` (1 to 500 characters), which approvers see |
| `run_id` | Yes | Groups actions from one conversation or task (1 to 128 characters) |
| `idempotency_key` | Yes | Unique per intended action; send the same key to retry safely (1 to 128 characters) |
| `signals` | No | What your app knows about the request; feeds identity and address checks |

### Action types

| `type` | `params` |
|---|---|
| `refund` | `orderId`, `amountCents`, `reason` |
| `store_credit` | `customerId`, `amountCents`, `reason` |
| `cancel_order` | `orderId`, `reason` |
| `update_shipping_address` | `orderId`, `newAddress` (`line1`, `city`, `region`, `postalCode`, `country` as a 2-letter code), `reason` |
| `update_account_email` | `customerId`, `newEmail`, `reason` |
| `create_discount_code` | `customerId`, `percentOff` (1 to 100), `expiresInDays` (1 to 365), `reason` |

Need another action type? [Request it](../../../issues/new/choose).

### Response

`201` for a new action, `200` when the idempotency key was already used for the same request (you get the first result back).

```json
{
  "action_id": "6f0c…",
  "type": "refund",
  "status": "held",
  "decision": "hold",
  "enforced": true,
  "reasons": ["approval_required"],
  "message": "Held for approval. This is above the approval threshold, so it needs approval.",
  "receipt_ids": ["urn:uuid:…"],
  "created_at": "2026-10-16T19:53:01.000Z",
  "updated_at": "2026-10-16T19:53:01.000Z"
}
```

| Field | Meaning |
|---|---|
| `status` | See the table below |
| `decision` | `allow`, `hold` or `deny` |
| `enforced` | `false` when the agent is in Observe mode: the decision was recorded, not applied |
| `would_have` | Observe mode only: `blocked` or `held` |
| `reasons` | Codes, see below |
| `message` | Plain-language summary your agent can pass on |
| `target_ref` | Store or payment ID, once executed |
| `output` | What the agent needs back, for example `{ "code": "…" }` for a discount code |
| `receipt_ids` | The sealed records for this action |
| `sealing` | `pending` while a record waits for the sealing service |
| `authorization` | Decision-only mode: `{ token, expires_at }` for your executor |
| `executed_by`, `outcome` | Decision-only mode: who ran it, and whether Tridris found it in your store (`verified`, `missing`, `mismatch`) |

### Statuses

| `status` | Meaning | What your agent should say |
|---|---|---|
| `executed` | Within limits and done | Confirm it |
| `held` | Waiting for a person | It's waiting for approval; never that it's done |
| `denied` | Outside the limits | Explain `message` and offer an alternative |
| `approved` | Cleared; Decision-only mode: your system runs it | (your system acts) |
| `executing` | Running now | Wait and check again |
| `rejected` | A person said no | Say so |
| `expired` | Nobody decided in time | Say so; nothing changed |
| `failed` | The store or payment system did not complete it | Say so; nothing changed |

### Reason codes

| Code | Meaning |
|---|---|
| `within_limits` | Within all limits |
| `agent_inactive` | This agent is switched off |
| `action_not_allowed` | This agent may not take this action type |
| `velocity_exceeded` | Hourly limit of actions reached |
| `customer_action_limit` | Daily limit of actions for this customer reached |
| `over_max_per_action` | Above the maximum for one action |
| `exceeds_refundable_amount` | More than is left to refund on the order |
| `daily_budget_exceeded` | Would go over the daily money limit |
| `customer_limit_review` | Would go over the customer's 30-day money limit, so it needs approval |
| `approval_required` | Above the approval threshold |
| `approval_always_required` | This action type always needs approval for this agent |
| `action_daily_limit` | Daily limit for this action type reached |
| `action_money_limit` | Would go over the daily money limit for this action type |
| `outside_working_hours` | Outside the working hours set for the agent |
| `order_already_cancelled` | The order is already cancelled |
| `order_already_fulfilled` | The order has shipped; the customer needs a return |
| `order_value_too_high` | The order is above the largest value the agent may cancel |
| `order_being_packed` | The order is being packed, so it can no longer be cancelled |
| `fulfillment_in_progress` | The order is being packed, so cancelling needs approval |
| `order_already_shipped` | Shipped or being packed, so the address can't change |
| `address_region_changed` | The new address is in another country or region |
| `recent_contact_change` | The customer's contact details changed recently |
| `repeated_identity_change` | Contact details changed recently, so another change is not allowed |
| `high_value_order` | A high-value order |
| `identity_change_requires_approval` | Changing the account email always needs approval |
| `new_device`, `location_mismatch` | From the `signals` you sent |
| `over_max_discount` | Discount above the maximum |
| `daily_code_limit` | Daily limit of discount codes reached |
| `repeat_discount_review` | The customer had a code recently |
| `system_unavailable` | A required check was unavailable, so nothing ran |
| `execution_failed` | The store or payment system did not complete it |
| `approval_rejected`, `approval_expired`, `authorization_expired` | After a hold or authorization |

## GET /v1/actions/{action_id}

Returns the same response shape. Only your own agent's actions; anything else is `404`. Poll every few seconds while the status is `held`, `approved` or `executing`.

## POST /v1/actions/{action_id}/result

Decision-only mode. After your system runs (or fails to run) an authorized action:

```json
{ "outcome": "executed", "target_ref": "re_3P…", "output": { "note": "optional" } }
```

`outcome` is `executed` or `failed`. Tridris seals the result and checks your store, read-only, that it really happened.

## GET /v1/demo/store

```json
{
  "customers": [{ "id": "…", "name": "Sam Rivera" }],
  "orders": [{ "id": "…", "number": "#1001", "customer_id": "…", "total_cents": 210000, "refundable_cents": 210000, "status": "open", "fulfillment": "unfulfilled" }]
}
```

Made-up data. IDs change when the demo is reset.

## Errors

Errors are JSON with `error` and `message`.

| HTTP | `error` | What to do |
|---|---|---|
| 400 | `invalid_request` | Fix the request; `message` names the field |
| 401 | `unauthorized` | Check the agent token |
| 404 | `not_found` | Not one of your agent's actions, or a wrong ID |
| 409 | `idempotency_conflict` | That key was used for a different request; use a new key |
| 503 | `system_unavailable` | Nothing ran. Retry with the same idempotency key |

Tridris fails closed: if a check, its database or the sealing service is unavailable, the action does not run.
