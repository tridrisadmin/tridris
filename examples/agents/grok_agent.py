"""A customer-support agent on Grok (xAI) whose actions go through Tridris.

xAI's API is compatible with the OpenAI SDK, so this reuses openai_agent.py with xAI's address and key.

    pip install openai
    export XAI_API_KEY=...  XAI_MODEL=<a current Grok model that supports function calling>
    export TRIDRIS_URL=...  TRIDRIS_AGENT_TOKEN=...
    python grok_agent.py
"""
import os

from openai import OpenAI

from openai_agent import chat

if __name__ == "__main__":
    chat(OpenAI(api_key=os.environ["XAI_API_KEY"], base_url="https://api.x.ai/v1"), os.environ["XAI_MODEL"], "grok")
