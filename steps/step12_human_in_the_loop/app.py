"""Step 12 - Human in the loop.

Barista Bot can now issue refunds, but never on its own: the agent pauses before every refund,
a human approves, edits or rejects it, and the agent carries on from exactly where it stopped.
"""

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, ModelRequest, dynamic_prompt
from langchain.chat_models import init_chat_model
from langchain.tools import ToolRuntime, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from guardrails import guardrails  # CHANGED: step 11's middleware, moved out
from knowledge import build_index, search_handbook
from shared import MODEL, print_updates, run_demo
from shared.shop import CUSTOMERS, ORDERS
from shop_tools import (
    CustomerContext,
    check_stock,
    get_order_status,
    list_my_orders,
    search_products,
)

model = init_chat_model(MODEL)


# NEW: a tool that changes something in the real world (here, pretend it moves money).
@tool
def issue_refund(
    order_id: str, amount_inr: int, reason: str, runtime: ToolRuntime[CustomerContext]
) -> dict:
    """Refund money to the customer for one of their orders. A human approves every refund.

    Args:
        order_id: The order number, like "BS-1002".
        amount_inr: How much to refund, in whole rupees. At most the order total.
        reason: One short sentence explaining why, for the approver.
    """
    order = ORDERS.get(order_id.strip().upper())
    if order is None or order["customer_id"] != runtime.context.customer_id:
        return {"error": f"No order {order_id} on this customer's account."}
    if order["status"] == "cancelled":
        return {"error": f"Order {order_id} was cancelled and never charged. Nothing to refund."}
    if not 0 < amount_inr <= order["total"]:
        return {"error": f"Refund must be between ₹1 and the order total, ₹{order['total']}."}
    return {
        "status": "refund issued",
        "order_id": order_id,
        "amount_inr": amount_inr,
        "arrives_in": "5 to 7 working days, to the original payment method",
    }


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
- Before a refund, check the order and the refund policy, then call issue_refund. Never say a
  refund is done unless issue_refund returned "refund issued".

TOOLS
- search_handbook: any question about shipping, returns, refunds, warranty, Bean Points or brewing.
- list_my_orders: when the customer asks about "my orders" or "my last order" without a number.
- get_order_status: any question about one order.
- search_products: to find products, and their ids and prices.
- check_stock: to check stock for a product id from search_products.
- issue_refund: to refund an order, when the refund policy allows it.

FORMAT
- At most five short sentences or bullet points.
"""  # CHANGED: a refund rule and a line for issue_refund


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
        search_handbook,
        list_my_orders,
        get_order_status,
        search_products,
        check_stock,
        issue_refund,  # NEW
    ],
    middleware=[
        personalised_prompt,
        *guardrails(model),
        # NEW: pause before every issue_refund call and wait for a human decision.
        # Tools that are not listed run without asking.
        HumanInTheLoopMiddleware(
            interrupt_on={
                "issue_refund": {
                    "allowed_decisions": ["approve", "edit", "reject"],
                    "description": "Refund requested. Check it against the refund policy.",
                }
            }
        ),
    ],
    context_schema=CustomerContext,
    # A checkpointer is required: the paused run is saved there until the human decides.
    checkpointer=InMemorySaver(),
)


# NEW: the human side. Shows the paused tool call and asks for a decision in the terminal.
# In a real app this would be a button in a support dashboard.
def review(action: dict) -> dict:
    print(f"\n[review] {action['description']}")
    print(f"[review] {action['name']}({action['args']})")
    choice = input("[review] approve (a), edit the amount (e) or reject (r)? ").strip().lower()
    print()

    if choice == "a":
        return {"type": "approve"}
    if choice == "e":
        amount = int(input("[review] new amount in ₹: "))
        new_args = {**action["args"], "amount_inr": amount}
        return {"type": "edit", "edited_action": {"name": action["name"], "args": new_args}}
    reason = input("[review] reason, for Barista Bot to pass on: ")
    return {"type": "reject", "message": reason}


def ask(question: str, customer_id: str = "C-001") -> None:
    config = {"configurable": {"thread_id": customer_id}}
    context = CustomerContext(customer_id=customer_id)
    agent_input = {"messages": [{"role": "user", "content": question}]}

    # NEW: run until the agent finishes. If it pauses for a human, collect the decisions and
    # resume it with Command(resume=...): the same thread, carrying on where it stopped.
    while True:
        for chunk in agent.stream(agent_input, config, context=context, stream_mode="updates"):
            print_updates(chunk)

        interrupts = agent.get_state(config).interrupts  # empty when the agent finished
        if not interrupts:
            break
        # One interrupt can hold several tool calls to review; answer each one, in order.
        decisions = [review(action) for action in interrupts[0].value["action_requests"]]
        agent_input = Command(resume={"decisions": decisions})


DEMO_PROMPTS = [  # CHANGED: this step's prompts. Try approve, reject, then edit.
    (
        "One bag of beans in order BS-1001 arrived torn and half empty. Please refund that bag.",
        "C-001",
    ),
    ("The second bag in that order was torn too. Refund it as well.", "C-001"),
    ("Please cancel my order BS-1003 and refund me.", "C-002"),
]

if __name__ == "__main__":
    build_index()
    run_demo(ask, DEMO_PROMPTS)
