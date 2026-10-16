"""One action tool in plain Python (standard library only): ask Tridris, then tell the agent what happened.

    export TRIDRIS_URL=... TRIDRIS_AGENT_TOKEN=...
    python refund_tool.py <order ID> <amount in cents>
"""
import json
import os
import sys
import urllib.error
import urllib.request


def issue_refund(order_id: str, amount_cents: int, reason: str, run_id: str, ticket_id: str) -> dict:
    req = urllib.request.Request(
        f"{os.environ['TRIDRIS_URL'].rstrip('/')}/v1/actions",
        method="POST",
        data=json.dumps({
            "type": "refund",
            "params": {"orderId": order_id, "amountCents": amount_cents, "reason": reason},
            "run_id": run_id,                        # groups every action from one conversation or task
            "idempotency_key": f"refund-{ticket_id}",  # reuse it when you retry: nothing runs twice
        }).encode(),
        headers={"Authorization": f"Bearer {os.environ['TRIDRIS_AGENT_TOKEN']}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            body = json.loads(res.read())
    except urllib.error.HTTPError as e:
        body = json.loads(e.read() or b"{}")
        # 503 system_unavailable: nothing ran. Tell the customer you'll try again shortly.
        return {"status": "error", "message": body.get("message", "Try again shortly.")}
    # executed: done · held: waiting for a person · denied: outside the limits (message says why)
    return {"status": body["status"], "message": body["message"], "action_id": body["action_id"]}


if __name__ == "__main__":
    print(json.dumps(issue_refund(sys.argv[1], int(sys.argv[2]), "Arrived damaged", "example-run", f"ticket-{os.getpid()}"), indent=2))
