"""Step 14 example - Long-term memory with a store.

The checkpointer (step 07) remembers one conversation. A store remembers facts across ALL of a
customer's conversations: here, their favourite roast. Two different threads, one memory.

    python steps/step14_next_level/long_term_memory.py
"""

from dataclasses import dataclass

from langchain.agents import create_agent
from langchain.tools import ToolRuntime, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from shared import MODEL, print_updates, run_demo
from shared.shop import PRODUCTS


@dataclass
class CustomerContext:
    customer_id: str


# A store holds JSON documents under a namespace (a tuple) and a key.
# InMemoryStore is for learning; PostgresStore and others keep it for real.
store = InMemoryStore()


@tool
def save_preference(preference: str, runtime: ToolRuntime[CustomerContext]) -> str:
    """Remember something the customer likes, for future conversations.

    Args:
        preference: A short fact, like "favourite roast: Monsoon Malabar".
    """
    namespace = ("preferences", runtime.context.customer_id)
    saved = runtime.store.get(namespace, "notes")
    notes = saved.value["notes"] if saved else []
    runtime.store.put(namespace, "notes", {"notes": [*notes, preference]})
    return "Saved."


@tool
def recall_preferences(runtime: ToolRuntime[CustomerContext]) -> list[str]:
    """Recall what the customer told us they like, in earlier conversations."""
    saved = runtime.store.get(("preferences", runtime.context.customer_id), "notes")
    return saved.value["notes"] if saved else []


@tool
def list_beans() -> list[dict]:
    """List the coffee beans Bean Street Coffee sells, with tasting notes."""
    return [
        {"name": p["name"], "notes": p["notes"]}
        for p in PRODUCTS.values()
        if p["category"] == "beans"
    ]


agent = create_agent(
    model=MODEL,  # create_agent also accepts a "provider:model" string
    tools=[save_preference, recall_preferences, list_beans],
    system_prompt=(
        "You are Barista Bot, the support assistant of Bean Street Coffee. Be brief. "
        "When the customer says what they like, save it. When they ask for a recommendation "
        "or what you remember, recall their preferences first. "
        "Only recommend beans from list_beans."
    ),
    context_schema=CustomerContext,
    checkpointer=InMemorySaver(),  # short-term: one conversation per thread
    store=store,  # long-term: shared by every thread
)


def ask(question: str, thread_id: str) -> None:
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        {"configurable": {"thread_id": thread_id}},
        context=CustomerContext(customer_id="C-001"),
        stream_mode="updates",
    ):
        print_updates(chunk)


if __name__ == "__main__":
    run_demo(
        ask,
        [
            ("I love dark, smoky coffee, and I brew with a South Indian filter.", "monday-chat"),
            ("Which of your beans would you pick for me?", "friday-chat"),  # a NEW thread
        ],
    )
