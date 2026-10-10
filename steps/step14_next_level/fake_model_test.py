"""Step 14 example - Test chains, tools and agents without calling a real model.

A fake chat model returns replies you script in advance, so tests are fast, free, need no API key
and give the same result every time. Runs with plain Python, or with pytest if you have it.

    python steps/step14_next_level/fake_model_test.py
"""

from langchain.agents import create_agent
from langchain.messages import AIMessage, ToolMessage
from langchain.tools import tool
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

ORDERS = {"BS-1002": {"status": "shipped", "courier": "BlueDart"}}


@tool
def get_order_status(order_id: str) -> dict:
    """Look up the status of a Bean Street Coffee order.

    Args:
        order_id: The order number, like "BS-1002".
    """
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"error": f"No order {order_id}."}
    return {"order_id": order_id, **order}


class FakeToolCallingModel(GenericFakeChatModel):
    """GenericFakeChatModel can't bind tools, which agents need. This version accepts the tools and
    ignores them: the scripted replies decide which tools get "called"."""

    def bind_tools(self, tools, **kwargs):
        return self


def test_tool_directly():
    # A tool is a plain object you can invoke with a dict of arguments. No model needed.
    assert get_order_status.invoke({"order_id": "bs-1002"})["status"] == "shipped"
    assert "error" in get_order_status.invoke({"order_id": "BS-9999"})


def test_chain_with_fake_model():
    fake = GenericFakeChatModel(messages=iter([AIMessage("Store beans in an airtight jar.")]))
    chain = ChatPromptTemplate.from_template("Answer: {question}") | fake | StrOutputParser()
    assert chain.invoke({"question": "How do I store beans?"}) == "Store beans in an airtight jar."


def test_agent_calls_tool_then_answers():
    # Script the model: first it asks for a tool call, then it gives the final answer.
    fake = FakeToolCallingModel(
        messages=iter(
            [
                AIMessage(
                    "",
                    tool_calls=[
                        {"name": "get_order_status", "args": {"order_id": "BS-1002"}, "id": "1"}
                    ],
                ),
                AIMessage("Your order BS-1002 has shipped with BlueDart."),
            ]
        )
    )
    agent = create_agent(model=fake, tools=[get_order_status])

    result = agent.invoke({"messages": [{"role": "user", "content": "Where is BS-1002?"}]})

    # The real tool ran, and its result went back into the conversation.
    tool_results = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_results) == 1
    assert '"status": "shipped"' in tool_results[0].content
    assert result["messages"][-1].text == "Your order BS-1002 has shipped with BlueDart."


if __name__ == "__main__":
    for test in (
        test_tool_directly,
        test_chain_with_fake_model,
        test_agent_calls_tool_then_answers,
    ):
        test()
        print(f"ok  {test.__name__}")
