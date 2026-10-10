"""Step 05 - First tool.

Barista Bot can now look up an order. You write a Python function, the model asks for it to be
called, and you run it and send back the result: the "tool loop", written out by hand.
"""

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage
from langchain.tools import tool

from shared import MODEL, print_message, run_demo
from shared.shop import ORDERS, PRODUCTS

model = init_chat_model(MODEL)


# NEW: @tool turns a function into a tool. Its name, type hints and docstring become the
# description the model reads, so write the docstring for the model.
@tool
def get_order_status(order_id: str) -> dict:
    """Look up the status of a Bean Street Coffee order.

    Args:
        order_id: The order number, like "BS-1002".
    """
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        # An expected problem is returned, not raised, so the model can read it and recover.
        return {"error": f"No order {order_id}. Order numbers look like BS-1002."}
    items = [PRODUCTS[product_id]["name"] for product_id in order["items"]]
    return {"order_id": order_id, **order, "items": items}


# NEW: bind_tools() sends the tools' descriptions to the model with every call.
# The model can now answer with a request to call a tool instead of (or as well as) text.
model_with_tools = model.bind_tools([get_order_status])

# CHANGED: Part 1 used prompt templates; for a tool loop we build the message list by hand,
# so you can see every message that goes back and forth.
SYSTEM_PROMPT = (
    "You are Barista Bot, the support assistant of Bean Street Coffee, an online coffee shop "
    "in India. Use get_order_status for any question about an order. "
    "Only state order details that a tool gave you. Answer in at most three short sentences."
)


def ask(question: str) -> None:
    messages = [SystemMessage(SYSTEM_PROMPT), HumanMessage(question)]

    # NEW: the tool loop. Repeat until the model answers without asking for a tool.
    while True:
        response = model_with_tools.invoke(messages)  # an AIMessage
        messages.append(response)
        print_message(response)  # prints tool calls as "->" and text as a reply

        if not response.tool_calls:
            break  # no tool requested: this is the final answer

        for tool_call in response.tool_calls:
            # tool_call is a dict: {"name": ..., "args": {...}, "id": ...}.
            # Invoking a tool with the whole tool_call returns a ToolMessage that carries the
            # call's id, so the model knows which request this result answers.
            tool_message = get_order_status.invoke(tool_call)
            messages.append(tool_message)
            print_message(tool_message)  # prints the result as "<-"


DEMO_PROMPTS = [  # CHANGED: this step's prompts
    "Where is my order BS-1002?",
    "Has BS-1003 shipped yet? And what about BS-1001?",
    "What's happening with order BS-9999?",
    "Do you have the Coorg Arabica beans in stock?",
]

if __name__ == "__main__":
    run_demo(ask, DEMO_PROMPTS)
