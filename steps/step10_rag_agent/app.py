"""Step 10 - RAG agent.

The second half of RAG: the agent searches the handbook with a tool, then answers from what it
found and says where it found it. Retrieval (step 09) + the agent (steps 06-08).
"""

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from knowledge import build_index, vector_store  # CHANGED: step 09's index, moved out
from shared import MODEL, print_updates, run_demo
from shared.shop import CUSTOMERS
from shop_tools import (  # CHANGED: step 08's tools and context, moved out
    CustomerContext,
    check_stock,
    get_order_status,
    list_my_orders,
    search_products,
)

model = init_chat_model(MODEL)


# NEW: retrieval as a tool. The agent decides when to search and what to search for.
@tool
def search_handbook(query: str) -> str:
    """Search Bean Street Coffee's policy handbook: shipping, returns, refunds, warranty,
    the Bean Points loyalty programme, and brewing guides.

    Args:
        query: What to look for, in plain words, like "return opened beans".
    """
    chunks = vector_store.similarity_search(query, k=3)
    # Label every chunk with where it came from, so the model can cite it.
    return "\n\n".join(
        f"[{chunk.metadata['source']} > {chunk.metadata.get('section', 'intro')}]\n"
        f"{chunk.page_content}"
        for chunk in chunks
    )


SYSTEM_PROMPT = """\
You are Barista Bot, the support assistant of Bean Street Coffee, an online coffee shop in India.

RULES
- Only help with Bean Street Coffee: orders, products, stock, policies and brewing.
  Politely decline anything else.
- Only state order, product, price or stock details that a tool gave you. Prices are in rupees (₹).
- If a tool returns an error or nothing, say so and suggest what the customer can do.
- Answer policy and brewing questions only from search_handbook results, never from general
  knowledge. End such answers with the source in brackets, like (returns_and_refunds.md > Refunds).
- If the handbook does not answer the question, say you don't know and offer to pass it to a human.

TOOLS
- search_handbook: any question about shipping, returns, refunds, warranty, Bean Points or brewing.
- list_my_orders: when the customer asks about "my orders" or "my last order" without a number.
- get_order_status: any question about one order.
- search_products: to find products, and their ids and prices.
- check_stock: to check stock for a product id from search_products.

FORMAT
- At most five short sentences or bullet points.
"""  # CHANGED: handbook rules and a line for search_handbook


@dynamic_prompt
def personalised_prompt(request: ModelRequest) -> str:
    customer = CUSTOMERS[request.runtime.context.customer_id]
    return (
        SYSTEM_PROMPT
        + "\nCUSTOMER\n"
        + f"- You are talking to {customer['name']}, a {customer['tier']} loyalty member "
        + f"with {customer['points']} Bean Points. Greet them by name.\n"
    )


agent = create_agent(
    model=model,
    tools=[
        search_handbook,  # NEW
        list_my_orders,
        get_order_status,
        search_products,
        check_stock,
    ],
    middleware=[personalised_prompt],
    context_schema=CustomerContext,
    checkpointer=InMemorySaver(),
)


def ask(question: str, customer_id: str = "C-001") -> None:
    config = {"configurable": {"thread_id": customer_id}}
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        config,
        context=CustomerContext(customer_id=customer_id),
        stream_mode="updates",
    ):
        print_updates(chunk)


DEMO_PROMPTS = [  # CHANGED: this step's prompts
    (
        "I opened one bag of beans from my last order and don't like the taste. Can I return it?",
        "C-001",
    ),
    ("Do I have to pay for express shipping?", "C-001"),
    ("Do I have to pay for express shipping?", "C-003"),
    ("How do I make South Indian filter coffee?", "C-003"),
    ("Can I pay with Bitcoin?", "C-003"),
]

if __name__ == "__main__":
    build_index()  # index the handbook once, before the first question
    run_demo(ask, DEMO_PROMPTS)
