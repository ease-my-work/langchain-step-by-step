"""Step 03 - Structured output.

Barista Bot reads a customer email and fills in a support ticket: a Python object with
fixed fields, instead of free text you would have to parse yourself.
"""

from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from shared import MODEL, run_demo

model = init_chat_model(MODEL)


# NEW: the shape we want back, as a Pydantic model. The field names, types and descriptions
# are sent to the model, so write them for the model to read.
class Ticket(BaseModel):
    """A support ticket created from one customer email."""

    category: Literal["order_status", "return_or_refund", "product_question", "complaint", "other"]
    priority: Literal["low", "normal", "urgent"] = Field(
        description="urgent: money lost, item broken or the customer is very upset. "
        "low: general questions."
    )
    order_id: str | None = Field(
        default=None,
        description='Order number like "BS-1002", only if the email mentions one.',
    )
    sentiment: Literal["positive", "neutral", "negative"]
    summary: str = Field(description="One short sentence saying what the customer wants.")


# CHANGED: the prompt now asks for triage, not for a reply.
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You triage customer emails for Bean Street Coffee, an online coffee shop."),
        ("human", "Customer email:\n\n{email}"),
    ]
)

# NEW: with_structured_output() makes the model return a Ticket instead of an AIMessage.
# REMOVED: StrOutputParser. The output is already a Python object.
chain = prompt | model.with_structured_output(Ticket)


def ask(email: str) -> None:
    ticket = chain.invoke({"email": email})  # a Ticket object, already validated by Pydantic

    # Ordinary Python from here on: no text parsing.
    print(f"[triage] {ticket.model_dump_json(indent=2)}")
    if ticket.priority == "urgent":
        print("[triage] -> urgent: send this one to a human straight away")


DEMO_PROMPTS = [  # CHANGED: customer emails instead of questions
    "Hi! Ordered an electric grinder last week (BS-1002). Any idea when it gets here? Thanks!",
    "This is the second time my beans arrived with a torn bag and coffee everywhere. "
    "Order BS-1001. I want my money back NOW.",
    "Do you have a decaf that works for cold brew?",
    "Loved the Monsoon Malabar, best coffee I've had all year!",
]

if __name__ == "__main__":
    run_demo(ask, DEMO_PROMPTS)
