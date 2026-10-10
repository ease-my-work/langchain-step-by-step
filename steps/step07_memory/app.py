"""Step 07 - Memory.

A checkpointer saves the conversation after every step of the agent, keyed by a thread id.
Send the next message with the same thread id and Barista Bot remembers what was said;
send it with a new thread id and it starts fresh.
"""

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver

from shared import MODEL, print_updates, run_demo
from shop_tools import check_stock, get_order_status, search_products  # CHANGED: moved out

model = init_chat_model(MODEL)

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
"""

# NEW: a checkpointer stores every conversation, one per thread id.
# InMemorySaver keeps them in this Python process, so they are gone when the script ends.
# In production you would use a database-backed one, such as PostgresSaver.
checkpointer = InMemorySaver()

agent = create_agent(
    model=model,
    tools=[get_order_status, search_products, check_stock],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,  # NEW
)


def ask(question: str, thread_id: str = "chat-1") -> None:  # CHANGED: takes a thread id
    # NEW: the config says which conversation (thread) this message belongs to.
    config = {"configurable": {"thread_id": thread_id}}

    # Send only the NEW message. The agent loads the earlier ones from the checkpointer.
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        config,  # NEW
        stream_mode="updates",
    ):
        print_updates(chunk)

    # NEW: get_state() reads what the checkpointer saved for this thread.
    saved = agent.get_state(config).values["messages"]
    print(f"  (thread {thread_id!r} now holds {len(saved)} messages)")


DEMO_PROMPTS = [  # CHANGED: (message, thread id) pairs
    ("Hi, I'm Asha. Where is my order BS-1002?", "asha"),
    ("Which courier has it? And remind me, what's my name?", "asha"),
    ("Is the decaf in stock? I'd like to add it to that order.", "asha"),
    ("What's my name, and which order did I ask about?", "rahul"),
    ("Where is order BS-1002?", "rahul"),
]

if __name__ == "__main__":
    run_demo(ask, DEMO_PROMPTS)
