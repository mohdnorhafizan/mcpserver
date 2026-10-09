import os

from dotenv import load_dotenv
from openai import OpenAI
from mcp.server.fastmcp import FastMCP

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

mcp = FastMCP("ChatGPT MCP Server")


@mcp.tool()
def ask_chatgpt(prompt: str) -> str:
    """Ask ChatGPT a question."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )

    return response.choices[0].message.content


@mcp.tool()
def summarize(text: str) -> str:
    """Summarize text."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Summarize the following:\n\n{text}"}],
    )

    return response.choices[0].message.content


@mcp.tool()
def explain_python(code: str) -> str:
    """Explain Python code."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Explain this Python code:\n\n{code}"}],
    )

    return response.choices[0].message.content


if __name__ == "__main__":
    mcp.run()