"""Tridris action tools for a customer-support agent, shared by the Claude, OpenAI, Gemini and Grok examples.

The model sees these tool definitions and the results; it never sees the Tridris token. Each action tool asks
Tridris first: the action runs, waits for a person to approve, or is blocked, and every outcome is recorded.
Standard library only.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid

TRIDRIS_URL = os.environ.get("TRIDRIS_URL", "").rstrip("/")
TRIDRIS_AGENT_TOKEN = os.environ.get("TRIDRIS_AGENT_TOKEN", "")

SYSTEM_PROMPT = (
    "You are a customer-support agent for an online store. Use the tools to look up orders and to take actions. "
    "Every action goes through Tridris, which decides whether it runs now, waits for a person to approve, or is blocked. "
    "Tell the customer exactly what happened, using the tool's message: never say an action is done unless its status "
    "is 'executed'. If it is 'held', say it is waiting for approval. If it is 'denied', explain why in plain words and "
    "offer an alternative. Amounts are in cents in tools and in dollars when you talk to the customer."
)

_reason = {"type": "string", "description": "Short reason for the record, in plain words, for example 'Arrived late'."}
_cents = {"type": "integer", "description": "Amount in cents, for example 2500 for $25.00."}

# Provider-neutral tool definitions: name, description and a JSON Schema for the arguments.
TOOLS: list[dict] = [
    {
        "name": "list_orders",
        "description": "The store's customers and orders: order ID and number, customer ID and name, total, amount still refundable and status.",
        "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
    },
    {
        "name": "refund",
        "description": "Refund money to the original payment for an order.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}, "amount_cents": _cents, "reason": _reason},
            "required": ["order_id", "amount_cents", "reason"],
            "additionalProperties": False,
        },
    },
    {
        "name": "store_credit",
        "description": "Give a customer store credit as goodwill.",
        "parameters": {
            "type": "object",
            "properties": {"customer_id": {"type": "string"}, "amount_cents": _cents, "reason": _reason},
            "required": ["customer_id", "amount_cents", "reason"],
            "additionalProperties": False,
        },
    },
    {
        "name": "cancel_order",
        "description": "Cancel an order that has not shipped.",
        "parameters": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}, "reason": _reason},
            "required": ["order_id", "reason"],
            "additionalProperties": False,
        },
    },
    {
        "name": "create_discount_code",
        "description": "Create a one-time discount code for a customer.",
        "parameters": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "percent_off": {"type": "integer", "description": "1 to 100."},
                "expires_in_days": {"type": "integer", "description": "1 to 365."},
                "reason": _reason,
            },
            "required": ["customer_id", "percent_off", "expires_in_days", "reason"],
            "additionalProperties": False,
        },
    },
    {
        "name": "check_action",
        "description": "Check whether an action that was waiting for approval has been approved, rejected or has expired.",
        "parameters": {
            "type": "object",
            "properties": {"action_id": {"type": "string"}},
            "required": ["action_id"],
            "additionalProperties": False,
        },
    },
]


def _call(method: str, path: str, body: dict | None = None) -> dict:
    if not TRIDRIS_URL or not TRIDRIS_AGENT_TOKEN:
        raise SystemExit("Set TRIDRIS_URL and TRIDRIS_AGENT_TOKEN first (from your Tridris access kit).")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(TRIDRIS_URL + path, data=data, method=method)
    req.add_header("Authorization", f"Bearer {TRIDRIS_AGENT_TOKEN}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return json.loads(res.read() or b"{}")
    except urllib.error.HTTPError as e:
        err = json.loads(e.read() or b"{}")
        # 503 system_unavailable means nothing ran: Tridris fails closed.
        return {"status": "error", "error": err.get("error", str(e.code)), "message": err.get("message", "Request failed.")}
    except urllib.error.URLError:
        return {"status": "error", "error": "unreachable", "message": "Tridris could not be reached, so nothing ran. Try again shortly."}


def _act(run_id: str, action_type: str, params: dict) -> dict:
    res = _call("POST", "/v1/actions", {
        "type": action_type,
        "params": params,
        "run_id": run_id,
        # A fresh key per tool call. To retry the same call safely, reuse its key.
        "idempotency_key": f"{action_type}-{uuid.uuid4()}",
    })
    keep = ("action_id", "status", "message", "reasons", "output")
    return {k: res[k] for k in keep if k in res} if res.get("status") != "error" else res


def run_tool(name: str, args: dict, run_id: str) -> str:
    """Runs one tool call and returns the result as a JSON string for the model."""
    if name == "list_orders":
        store = _call("GET", "/v1/demo/store")
        result: dict = store
    elif name == "refund":
        result = _act(run_id, "refund", {"orderId": args["order_id"], "amountCents": args["amount_cents"], "reason": args["reason"]})
    elif name == "store_credit":
        result = _act(run_id, "store_credit", {"customerId": args["customer_id"], "amountCents": args["amount_cents"], "reason": args["reason"]})
    elif name == "cancel_order":
        result = _act(run_id, "cancel_order", {"orderId": args["order_id"], "reason": args["reason"]})
    elif name == "create_discount_code":
        result = _act(run_id, "create_discount_code", {
            "customerId": args["customer_id"], "percentOff": args["percent_off"],
            "expiresInDays": args["expires_in_days"], "reason": args["reason"],
        })
    elif name == "check_action":
        res = _call("GET", f"/v1/actions/{args['action_id']}")
        result = {k: res[k] for k in ("action_id", "status", "message") if k in res} if res.get("status") != "error" else res
    else:
        result = {"status": "error", "message": f"Unknown tool {name}."}
    return json.dumps(result)


def new_run_id(provider: str) -> str:
    """Groups every action from one conversation in Tridris."""
    return f"{provider}-chat-{uuid.uuid4().hex[:8]}"
