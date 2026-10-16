# n8n: an HTTP Request node that asks Tridris

*Example, not yet tested by us.*

Put this node where your workflow would call your payment or store system.

| Setting | Value |
|---|---|
| Method | `POST` |
| URL | `{{$env.TRIDRIS_URL}}/v1/actions` |
| Authentication | Generic credential → Header Auth: name `Authorization`, value `Bearer <agent token>` (stored as a credential, not in the workflow) |
| Body content type | JSON |
| Body | `{"type":"refund","params":{"orderId":"{{$json.orderId}}","amountCents":{{$json.amountCents}},"reason":"{{$json.reason}}"},"run_id":"{{$execution.id}}","idempotency_key":"refund-{{$json.ticketId}}"}` |
| Options → Response | Never error (so you can branch on 4xx and 5xx answers) |

Then add a **Switch** node on `{{$json.status}}`:

- `executed`: continue (tell the customer it's done).
- `held`: tell the customer it's waiting for approval. Optionally add a Wait node and check `GET {{$env.TRIDRIS_URL}}/v1/actions/{{$json.action_id}}` later.
- `denied`: send `{{$json.message}}` back to the agent or customer and offer an alternative.
- Anything else (for example `system_unavailable`): nothing ran; retry later with the same idempotency key.
