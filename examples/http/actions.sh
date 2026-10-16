#!/usr/bin/env bash
# The three outcomes with curl: runs, waits for a person, blocked.
#   export TRIDRIS_URL=... TRIDRIS_AGENT_TOKEN=...
#   ./actions.sh <customer ID>        (find one with: curl "$TRIDRIS_URL/v1/demo/store" -H "Authorization: Bearer $TRIDRIS_AGENT_TOKEN")
set -euo pipefail
customer="${1:?Pass a customer ID}"
for cents in 2500 30000 90000; do
  curl -s -X POST "$TRIDRIS_URL/v1/actions" \
    -H "Authorization: Bearer $TRIDRIS_AGENT_TOKEN" -H "Content-Type: application/json" \
    -d "{\"type\":\"store_credit\",\"params\":{\"customerId\":\"$customer\",\"amountCents\":$cents,\"reason\":\"Late delivery\"},\"run_id\":\"curl-example\",\"idempotency_key\":\"curl-$cents-$(date +%s)\"}"
  echo
done
