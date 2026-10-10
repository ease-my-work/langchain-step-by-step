"""Step 14 example - Your own workflow with LangGraph.

create_agent() is built on LangGraph: a graph of steps ("nodes") that share a state.
When you want a fixed process instead of letting the model decide, draw the graph yourself.
This is step 04's email triage as a graph: triage, then route in code, then reply.

    START -> triage -> (urgent?) -> escalate -> END
                                 -> reply    -> END

    python steps/step14_next_level/custom_graph.py
"""

from typing import Literal, TypedDict

from langchain.chat_models import init_chat_model
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel

from shared import MODEL, run_demo

model = init_chat_model(MODEL)


class Ticket(BaseModel):
    category: Literal["order_status", "return_or_refund", "product_question", "complaint", "other"]
    priority: Literal["low", "normal", "urgent"]


# 1. The state: what every node can read. Each node returns the keys it wants to update.
class EmailState(TypedDict, total=False):
    email: str
    ticket: Ticket
    reply: str


# 2. Nodes: plain functions that take the state and return an update.
def triage(state: EmailState) -> dict:
    ticket = model.with_structured_output(Ticket).invoke(
        f"Triage this email to Bean Street Coffee, an online coffee shop:\n\n{state['email']}"
    )
    return {"ticket": ticket}


def reply(state: EmailState) -> dict:
    answer = model.invoke(
        "You are Barista Bot of Bean Street Coffee. Write a 2-sentence friendly reply. "
        f"Promise nothing; a human will check details.\n\n{state['email']}"
    )
    return {"reply": answer.text}


def escalate(state: EmailState) -> dict:
    return {"reply": "Sorry about this. A senior team member will call you within 4 hours."}


# 3. A routing function: reads the state and names the next node.
def route(state: EmailState) -> Literal["escalate", "reply"]:
    return "escalate" if state["ticket"].priority == "urgent" else "reply"


# 4. Wire it up and compile. The compiled graph has invoke(), stream() and batch(), like a chain
#    or an agent, and takes a checkpointer, so memory and human-in-the-loop work here too.
builder = StateGraph(EmailState)
builder.add_node("triage", triage)
builder.add_node("reply", reply)
builder.add_node("escalate", escalate)
builder.add_edge(START, "triage")
builder.add_conditional_edges("triage", route)
builder.add_edge("reply", END)
builder.add_edge("escalate", END)
graph = builder.compile()


def ask(email: str) -> None:
    result = graph.invoke({"email": email})
    print(f"[triage] {result['ticket'].category}, {result['ticket'].priority}")
    print(f"[reply] {result['reply']}")


if __name__ == "__main__":
    print(graph.get_graph().draw_mermaid())  # paste into https://mermaid.live to see it
    run_demo(
        ask,
        [
            "Is the Coorg Arabica back in stock yet?",
            "My espresso machine sparked and the kitchen smells of smoke! Order BS-1004.",
        ],
    )
