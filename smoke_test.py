"""Checks that the key, model, and tool calling all work together."""

import os

from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

load_dotenv()


@tool
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL"), use_responses_api=True)

print("Plain call:", llm.invoke("Say hello in five words.").content)

response = llm.bind_tools([add]).invoke("What is 17 plus 25? Use the tool.")
print("Tool calls:", response.tool_calls)