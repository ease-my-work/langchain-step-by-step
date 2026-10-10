"""Step 11 - Middleware.

Middleware is code that runs around the agent's loop: before or after each model call, or around
each tool call. LangChain ships ready-made middleware for common jobs, and you can write your own
with a decorator. Barista Bot gets guardrails that work in code, not just in the prompt.
"""

import time

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    ModelRequest,
    PIIMiddleware,
    SummarizationMiddleware,
    before_model,
    dynamic_prompt,
    wrap_tool_call,
)
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime

from knowledge import build_index, search_handbook  # CHANGED: search_handbook moved out
from shared import MODEL, print_updates, run_demo
from shared.shop import CUSTOMERS
from shop_tools import (
    CustomerContext,
    check_stock,
    get_order_status,
    list_my_orders,
    search_products,
)

model = init_chat_model(MODEL)

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
"""


@dynamic_prompt
def personalised_prompt(request: ModelRequest) -> str:
    customer = CUSTOMERS[request.runtime.context.customer_id]
    return (
        SYSTEM_PROMPT
        + "\nCUSTOMER\n"
        + f"- You are talking to {customer['name']}, a {customer['tier']} loyalty member "
        + f"with {customer['points']} Bean Points. Greet them by name.\n"
    )


# NEW: custom middleware, hook 1. @before_model runs before every model call and sees the state.
# This one only prints the latest user message as the model will receive it, so you can see the
# PII middleware below at work. Returning None means "change nothing".
@before_model
def show_what_model_sees(state: AgentState, runtime: Runtime) -> None:
    last_user_message = next(m for m in reversed(state["messages"]) if m.type == "human")
    print(f"[middleware] model sees: {last_user_message.text}")


# NEW: custom middleware, hook 2. @wrap_tool_call wraps every tool call: code before handler()
# runs before the tool, code after it runs after. Good for logging, timing, retries and caching.
@wrap_tool_call
def log_tool_calls(request, handler):
    started = time.perf_counter()
    result = handler(request)  # runs the tool
    took_ms = (time.perf_counter() - started) * 1000
    print(f"[middleware] {request.tool_call['name']} took {took_ms:.0f} ms")
    return result


agent = create_agent(
    model=model,
    tools=[search_handbook, list_my_orders, get_order_status, search_products, check_stock],
    middleware=[
        personalised_prompt,
        # NEW: built-in middleware. Hooks of the same kind run in this list's order.
        # Mask card numbers in user messages before the model sees them (or the checkpointer
        # saves them): "4111 1111 1111 1111" -> "****-****-****-1111".
        PIIMiddleware("credit_card", strategy="mask"),
        # Replace email addresses with a placeholder.
        PIIMiddleware("email", strategy="redact"),
        # Stop a run that calls the model more than 6 times: a loop that has gone wrong.
        ModelCallLimitMiddleware(run_limit=6, exit_behavior="end"),
        # When a thread passes 12 messages, summarise the older ones and keep the last 4,
        # so long chats stay short (and cheap) for the model.
        SummarizationMiddleware(model=model, trigger=("messages", 12), keep=("messages", 4)),
        show_what_model_sees,  # NEW: custom
        log_tool_calls,  # NEW: custom
    ],
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

    saved = agent.get_state(config).values["messages"]  # NEW: watch summarisation shrink this
    print(f"  (thread {customer_id!r} now holds {len(saved)} messages)")


DEMO_PROMPTS = [  # CHANGED: one long chat with Asha
    "My card 4111 1111 1111 1111 was charged twice for order BS-1002! "
    "Email the receipt to asha.r@example.com",
    "What does the warranty on that grinder cover?",
    "And how long do its burrs last?",
    "Is the decaf in stock?",
    "What did I first contact you about today?",
]

if __name__ == "__main__":
    build_index()
    run_demo(ask, DEMO_PROMPTS)
