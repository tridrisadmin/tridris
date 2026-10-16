"""A customer-support agent on Claude whose actions go through Tridris.

    pip install anthropic
    export ANTHROPIC_API_KEY=...  TRIDRIS_URL=...  TRIDRIS_AGENT_TOKEN=...
    python claude_agent.py
"""
import json

import anthropic

from tridris_tools import SYSTEM_PROMPT, TOOLS, new_run_id, run_tool

MODEL = "claude-opus-5-5"

client = anthropic.Anthropic()
tools = [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"], "strict": True} for t in TOOLS]


def reply(messages: list, run_id: str) -> str:
    while True:
        # Server-side fallbacks: if a request is declined by a safety classifier, it is retried on a suitable model.
        response = client.beta.messages.create(
            model=MODEL,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason == "refusal":
            return "Sorry, I can't help with that."
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")
        results = []
        for block in response.content:
            if block.type == "tool_use":
                output = run_tool(block.name, block.input, run_id)
                print(f"  [Tridris] {block.name} -> {json.loads(output).get('status', 'ok')}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
        messages.append({"role": "user", "content": results})


def main() -> None:
    run_id, messages = new_run_id("claude"), []
    print("Claude support agent. Type a customer message (Ctrl+C to quit).")
    while True:
        messages.append({"role": "user", "content": input("\nCustomer: ")})
        print(f"\nAgent: {reply(messages, run_id)}")


if __name__ == "__main__":
    main()
