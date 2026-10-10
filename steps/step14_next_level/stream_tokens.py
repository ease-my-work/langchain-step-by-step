"""Step 14 example - Stream an agent's reply token by token.

stream_mode="updates" (used in the course) gives you each finished step. For a chat window that
"types" the answer, use stream_mode="messages": it yields small message chunks as the model
writes them, from inside the agent loop.

    python steps/step14_next_level/stream_tokens.py
"""

from langchain.agents import create_agent
from langchain.tools import tool

from shared import MODEL, run_demo
from shared.shop import PRODUCTS


@tool
def list_brewers() -> list[str]:
    """List the brewers Bean Street Coffee sells."""
    return [p["name"] for p in PRODUCTS.values() if p["category"] == "brewers"]


agent = create_agent(
    model=MODEL,
    tools=[list_brewers],
    system_prompt="You are Barista Bot, the support assistant of Bean Street Coffee.",
)


def ask(question: str) -> None:
    # Each item is (message_chunk, metadata). metadata["langgraph_node"] says which node
    # produced it: "model" for the model's words, "tools" for tool results.
    for chunk, metadata in agent.stream(
        {"messages": [{"role": "user", "content": question}]}, stream_mode="messages"
    ):
        if metadata["langgraph_node"] == "model" and chunk.text:
            print(chunk.text, end="", flush=True)
        elif metadata["langgraph_node"] == "tools":
            print(f"\n[tool {chunk.name} finished]\n", flush=True)
    print()


if __name__ == "__main__":
    run_demo(ask, ["Compare every brewer you sell, in a short paragraph each."])
