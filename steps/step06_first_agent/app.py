"""Step 06 - First agent.

create_agent() runs the tool loop from step 05 for you. Barista Bot gets two more tools and
decides on its own which to call, in what order, and when it has enough to answer.
"""

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool

from shared import MODEL, print_updates, run_demo
from shared.shop import ORDERS, PRODUCTS

model = init_chat_model(MODEL)


@tool
def get_order_status(order_id: str) -> dict:
    """Look up the status of a Bean Street Coffee order.

    Args:
        order_id: The order number, like "BS-1002".
    """
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"error": f"No order {order_id}. Order numbers look like BS-1002."}
    items = [PRODUCTS[product_id]["name"] for product_id in order["items"]]
    return {"order_id": order_id, **order, "items": items}


# NEW: a tool to search the catalogue.
@tool
def search_products(query: str) -> list[dict]:
    """Search the Bean Street Coffee catalogue by keyword.

    Args:
        query: One or two words, like "decaf", "grinder" or "espresso".
            Categories are: beans, grinders, brewers, espresso machines.
    """
    words = query.lower().split()
    matches = []
    for product_id, product in PRODUCTS.items():
        text = f"{product['name']} {product['category']} {product['notes']}".lower()
        if any(word in text for word in words):
            matches.append(
                {"product_id": product_id, "name": product["name"], "price_inr": product["price"]}
            )
    return matches  # an empty list tells the model "nothing found"


# NEW: a tool to check stock. The model needs a product_id, which search_products returns,
# so it has to call the two tools in order.
@tool
def check_stock(product_id: str) -> dict:
    """Check how many units of a product are in stock, plus tasting or product notes.

    Args:
        product_id: The product id from search_products, like "BEAN-MAL".
    """
    product = PRODUCTS.get(product_id.strip().upper())
    if product is None:
        return {"error": f"No product {product_id}. Use search_products to find the id."}
    return {"product_id": product_id, "in_stock": product["stock"], "notes": product["notes"]}


SYSTEM_PROMPT = """\
You are Barista Bot, the support assistant of Bean Street Coffee, an online coffee shop in India.

RULES
- Only help with Bean Street Coffee: orders, products, stock and brewing.
  Politely decline anything else.
- Only state order, product, price or stock details that a tool gave you. Prices are in rupees (₹).
- If a tool returns an error or nothing, say so and suggest what the customer can do.

TOOLS
- get_order_status: any question about an order.
- search_products: to find products, and their ids and prices.
- check_stock: to check stock for a product id from search_products.

FORMAT
- At most four short sentences or bullet points.
"""  # CHANGED: rules and a TOOLS section for three tools

# NEW: the agent. It holds the model, the tools and the system prompt, and runs the
# model -> tools -> model loop until the model gives a final answer.
# REMOVED: model.bind_tools() and the hand-written while loop. create_agent does both.
agent = create_agent(
    model=model,
    tools=[get_order_status, search_products, check_stock],
    system_prompt=SYSTEM_PROMPT,
)


def ask(question: str) -> None:
    # CHANGED: the agent's input is a dict with a "messages" list. A message can be a
    # {"role": ..., "content": ...} dict instead of a HumanMessage object.
    # NEW: stream_mode="updates" yields one chunk each time a step of the loop finishes:
    # the model replied, or the tools ran. print_updates() prints them like step 05 did.
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="updates",
    ):
        print_updates(chunk)


DEMO_PROMPTS = [  # CHANGED: this step's prompts
    "Where is my order BS-1002?",
    "Do you have the Coorg Arabica beans in stock?",
    "I want a decaf for cold brew. What do you have, and is it in stock?",
    "Can you recommend a good laptop?",
    "I loved my last order. Can you send me the same again?",
]

if __name__ == "__main__":
    run_demo(ask, DEMO_PROMPTS)
