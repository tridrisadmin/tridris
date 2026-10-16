"""A customer-support agent on OpenAI whose actions go through Tridris.

    pip install openai
    export OPENAI_API_KEY=...  OPENAI_MODEL=<a current OpenAI model that supports function calling>
    export TRIDRIS_URL=...  TRIDRIS_AGENT_TOKEN=...
    python openai_agent.py

Grok uses the same code through xAI's OpenAI-compatible API: see grok_agent.py.
"""
import json
import os

from openai import OpenAI

from tridris_tools import SYSTEM_PROMPT, TOOLS, new_run_id, run_tool

tools = [{"type": "function", "function": {"name": t["name"], "description": t["description"], "parameters": t["parameters"]}} for t in TOOLS]


def reply(client: OpenAI, model: str, messages: list, run_id: str) -> str:
    while True:
        response = client.chat.completions.create(model=model, messages=messages, tools=tools)
        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))
        if not message.tool_calls:
            return message.content or ""
        for call in message.tool_calls:
            output = run_tool(call.function.name, json.loads(call.function.arguments or "{}"), run_id)
            print(f"  [Tridris] {call.function.name} -> {json.loads(output).get('status', 'ok')}")
            messages.append({"role": "tool", "tool_call_id": call.id, "content": output})


def chat(client: OpenAI, model: str, provider: str) -> None:
    run_id = new_run_id(provider)
    messages: list = [{"role": "system", "content": SYSTEM_PROMPT}]
    print(f"{provider.capitalize()} support agent ({model}). Type a customer message (Ctrl+C to quit).")
    while True:
        messages.append({"role": "user", "content": input("\nCustomer: ")})
        print(f"\nAgent: {reply(client, model, messages, run_id)}")


if __name__ == "__main__":
    chat(OpenAI(), os.environ["OPENAI_MODEL"], "openai")
