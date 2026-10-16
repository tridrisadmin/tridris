"""A customer-support agent on Gemini whose actions go through Tridris.

    pip install google-genai
    export GEMINI_API_KEY=...  GEMINI_MODEL=<a current Gemini model that supports function calling>
    export TRIDRIS_URL=...  TRIDRIS_AGENT_TOKEN=...
    python gemini_agent.py
"""
import json
import os

from google import genai
from google.genai import types

from tridris_tools import SYSTEM_PROMPT, TOOLS, new_run_id, run_tool

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = os.environ["GEMINI_MODEL"]
config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    tools=[types.Tool(function_declarations=[
        types.FunctionDeclaration(name=t["name"], description=t["description"], parameters_json_schema=t["parameters"]) for t in TOOLS
    ])],
    # This example runs the tools itself, so Tridris sees every call.
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


def reply(contents: list, run_id: str) -> str:
    while True:
        response = client.models.generate_content(model=MODEL, contents=contents, config=config)
        contents.append(response.candidates[0].content)
        if not response.function_calls:
            return response.text or ""
        parts = []
        for call in response.function_calls:
            output = run_tool(call.name, dict(call.args or {}), run_id)
            print(f"  [Tridris] {call.name} -> {json.loads(output).get('status', 'ok')}")
            parts.append(types.Part.from_function_response(name=call.name, response={"result": json.loads(output)}))
        contents.append(types.Content(role="user", parts=parts))


def main() -> None:
    run_id, contents = new_run_id("gemini"), []
    print(f"Gemini support agent ({MODEL}). Type a customer message (Ctrl+C to quit).")
    while True:
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=input("\nCustomer: "))]))
        print(f"\nAgent: {reply(contents, run_id)}")


if __name__ == "__main__":
    main()
