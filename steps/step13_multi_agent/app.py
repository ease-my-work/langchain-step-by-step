"""Step 13 - A team of agents.

One agent with many tools and a long prompt gets confused as it grows. Here Barista Bot becomes a
front desk with two specialists: an orders specialist and a policy specialist. Each specialist is a
full agent with its own prompt and tools, and the front desk calls them like tools.

    customer -> front desk -> ask_orders_specialist -> orders agent (order, product, stock tools)
                           -> ask_policy_specialist -> policy agent (handbook search)
                           -> issue_refund (a human approves)
"""

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware, ModelRequest, dynamic_prompt
from langchain.chat_models import init_chat_model
from langchain.tools import ToolRuntime, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from pydantic import BaseModel, Field

from guardrails import guardrails
from knowledge import build_index, search_handbook
from review import review  # CHANGED: step 12's reviewer, moved out
from shared import MODEL, print_updates, run_demo
from shared.shop import CUSTOMERS
from shop_tools import (  # CHANGED: issue_refund moved out too
    CustomerContext,
    check_stock,
    get_order_status,
    issue_refund,
    list_my_orders,
    search_products,
)

model = init_chat_model(MODEL)

# NEW: specialist 1, the orders agent. Its own short prompt and only the tools it needs.
orders_agent = create_agent(
    model=model,
    tools=[list_my_orders, get_order_status, search_products, check_stock],
    system_prompt=(
        "You are the orders specialist of Bean Street Coffee. Answer the request using your "
        "tools: orders, products, prices (in ₹) and stock. Report only facts the tools gave you, "
        "as short bullet points. You are talking to another agent, not the customer."
    ),
    context_schema=CustomerContext,  # its tools still need to know who is logged in
    name="orders_specialist",
)


# NEW: the shape of the policy specialist's answer.
class PolicyAnswer(BaseModel):
    answer: str = Field(description="The answer, using only what the handbook says.")
    sources: list[str] = Field(
        description='Where it came from, like "shipping.md > Shipping charges".'
    )
    found_in_handbook: bool = Field(description="False if the handbook does not answer it.")


# NEW: specialist 2, the policy agent. response_format makes the agent end with a PolicyAnswer
# object instead of free text, the agent version of with_structured_output() from step 03.
policy_agent = create_agent(
    model=model,
    tools=[search_handbook],
    system_prompt=(
        "You are the policy specialist of Bean Street Coffee. Search the handbook, then answer "
        "using only what it says. You are talking to another agent, not the customer."
    ),
    response_format=PolicyAnswer,
    name="policy_specialist",
)


# NEW: each specialist is wrapped in a tool, so the front desk calls it like any other tool.
# The tool's docstring is how the front desk knows when to use it.
@tool
def ask_orders_specialist(request: str, runtime: ToolRuntime[CustomerContext]) -> str:
    """Ask the orders specialist about the customer's orders, products, prices or stock.

    Args:
        request: The full question, with any order numbers or product names in it.
    """
    result = orders_agent.invoke(
        {"messages": [{"role": "user", "content": request}]},
        # The logged-in customer, passed on explicitly. (A sub-agent run inside a tool would
        # inherit it anyway, but saying so makes the data flow easy to see.)
        context=runtime.context,
    )
    return result["messages"][-1].text  # only the specialist's final answer goes back


@tool
def ask_policy_specialist(question: str) -> dict:
    """Ask the policy specialist about shipping, returns, refunds, warranty, Bean Points or brewing.

    Args:
        question: The policy or brewing question, in plain words.
    """
    result = policy_agent.invoke({"messages": [{"role": "user", "content": question}]})
    return result["structured_response"].model_dump()  # the PolicyAnswer, as a dict


SYSTEM_PROMPT = """\
You are Barista Bot, the front desk of Bean Street Coffee, an online coffee shop in India.
You don't look things up yourself: you ask your specialists, then answer the customer.

RULES
- Only help with Bean Street Coffee: orders, products, stock, policies and brewing.
  Politely decline anything else.
- Only state facts that a specialist gave you. Prices are in rupees (₹).
- For policy answers, end with the specialist's sources in brackets, like
  (shipping.md > Shipping charges). If found_in_handbook is false, say you don't know and
  offer to pass it to a human.
- Before a refund, check the order with the orders specialist and the refund policy with the
  policy specialist, then call issue_refund. Never say a refund is done unless issue_refund
  returned "refund issued".

TOOLS
- ask_orders_specialist: orders, products, prices and stock.
- ask_policy_specialist: shipping, returns, refunds, warranty, Bean Points and brewing.
- issue_refund: to refund an order, when the refund policy allows it.
  You can call both specialists at the same time when a question needs both.

FORMAT
- At most five short sentences or bullet points.
"""  # CHANGED: a front-desk prompt that delegates to specialists


@dynamic_prompt
def personalised_prompt(request: ModelRequest) -> str:
    customer = CUSTOMERS[request.runtime.context.customer_id]
    return (
        SYSTEM_PROMPT
        + "\nCUSTOMER\n"
        + f"- You are talking to {customer['name']}, a {customer['tier']} loyalty member "
        + f"with {customer['points']} Bean Points. Greet them by name.\n"
    )


# CHANGED: the front desk. Three tools instead of six; refunds and the human check stay here,
# so specialists can only read, never move money.
agent = create_agent(
    model=model,
    tools=[ask_orders_specialist, ask_policy_specialist, issue_refund],  # CHANGED
    middleware=[
        personalised_prompt,
        *guardrails(model),
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
    checkpointer=InMemorySaver(),
    name="front_desk",  # NEW: a name, shown when its updates are printed
)


def ask(question: str, customer_id: str = "C-001") -> None:
    config = {"configurable": {"thread_id": customer_id}}
    context = CustomerContext(customer_id=customer_id)
    agent_input = {"messages": [{"role": "user", "content": question}]}

    while True:
        # NEW: subgraphs=True also streams the specialists' own steps, so you can watch them work.
        for chunk in agent.stream(
            agent_input, config, context=context, stream_mode="updates", subgraphs=True
        ):
            print_updates(chunk, author="front_desk")

        interrupts = agent.get_state(config).interrupts
        if not interrupts:
            break
        decisions = [review(action) for action in interrupts[0].value["action_requests"]]
        agent_input = Command(resume={"decisions": decisions})


DEMO_PROMPTS = [  # CHANGED: this step's prompts
    ("Do you have decaf in stock, and how do I make cold brew with it?", "C-003"),
    ("Is the grinder in my order BS-1002 still covered if its burrs go dull?", "C-001"),
    (
        "One bag of beans in order BS-1001 arrived torn and half empty. Please refund that bag.",
        "C-001",
    ),
]

if __name__ == "__main__":
    build_index()
    run_demo(ask, DEMO_PROMPTS)
