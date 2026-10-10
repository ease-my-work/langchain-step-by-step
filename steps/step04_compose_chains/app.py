"""Step 04 - Composing chains.

Small chains join into one triage pipeline: two chains run in parallel, code picks the next
chain, and .batch() works through a whole inbox at once.

    email -> [ triage ticket | detect language ]  (in parallel)
          -> urgent?  yes -> escalation reply
                      no  -> normal reply
"""

from operator import itemgetter
from typing import Literal

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableParallel, RunnablePassthrough
from pydantic import BaseModel, Field

from shared import MODEL, run_demo

model = init_chat_model(MODEL)


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


# Step 03's chain, unchanged apart from its name.
triage_chain = (  # CHANGED: renamed from `chain`
    ChatPromptTemplate.from_messages(
        [
            ("system", "You triage customer emails for Bean Street Coffee, an online coffee shop."),
            ("human", "Customer email:\n\n{email}"),
        ]
    )
    | model.with_structured_output(Ticket)
)

# NEW: a second small chain. It only names the email's language.
language_chain = (
    ChatPromptTemplate.from_template(
        "Which language is this email written in? Answer with the language name only.\n\n{email}"
    )
    | model
    | StrOutputParser()
)

# NEW: two reply chains. The pipeline picks one per email.
REPLY_RULES = (
    "You are Barista Bot, the support assistant of Bean Street Coffee. "
    "Write a short email reply (at most 4 sentences) in {language}. "
    "Never promise refunds, dates or prices; a human will check the details. "
    "Sign off as 'Barista Bot, Bean Street Coffee'."
)
reply_chain = (
    ChatPromptTemplate.from_messages(
        [("system", REPLY_RULES), ("human", "Reply to this email:\n\n{email}")]
    )
    | model
    | StrOutputParser()
)
escalation_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", REPLY_RULES),
            (
                "human",
                "This customer is upset. Apologise sincerely, and say a senior team member will "
                "contact them within 4 hours. Reply to this email:\n\n{email}",
            ),
        ]
    )
    | model
    | StrOutputParser()
)


# NEW: routing in plain Python. A function can return a chain; LangChain then runs that chain
# with the same input.
def choose_reply(inputs: dict):
    if inputs["ticket"].priority == "urgent":
        return escalation_chain
    return reply_chain


# NEW: the pipeline.
# 1. RunnableParallel runs every part in it at the same time, on the same input, and returns a
#    dict of their outputs. itemgetter("email") just copies the email from the input dict.
# 2. RunnablePassthrough.assign(reply=...) keeps that dict and adds a "reply" key to it.
# 3. RunnableLambda turns a plain function into a chain part.
pipeline = RunnableParallel(
    email=itemgetter("email"),
    ticket=triage_chain,
    language=language_chain,
) | RunnablePassthrough.assign(reply=RunnableLambda(choose_reply))


def ask(emails: list[str]) -> None:  # CHANGED: gets the whole inbox at once
    # NEW: .batch() runs the pipeline on every input, several at a time, and returns the results
    # in the same order. Each input is a dict, because the prompts read {email}.
    results = pipeline.batch([{"email": email} for email in emails])

    for result in results:
        ticket = result["ticket"]
        print(f"\n[email] {result['email']}")
        print(f"[triage] {ticket.category}, {ticket.priority}, language: {result['language']}")
        print(f"[reply] {result['reply']}")


DEMO_PROMPTS = [  # CHANGED: one inbox of emails, in different languages
    "Hi! Ordered an electric grinder last week (BS-1002). Any idea when it gets here? Thanks!",
    "This is the second time my beans arrived with a torn bag and coffee everywhere. "
    "Order BS-1001. I want my money back NOW.",
    "Namaste, kya aapke paas decaf coffee hai jo cold brew ke liye achhi ho?",
]

if __name__ == "__main__":
    run_demo(ask, DEMO_PROMPTS, all_at_once=True)  # CHANGED: the whole inbox in one call
