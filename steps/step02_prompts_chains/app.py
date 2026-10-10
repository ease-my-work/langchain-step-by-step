"""Step 02 - Prompts and chains.

A prompt template fills in the shop's details, a chain joins template -> model -> parser,
and .stream() prints the reply word by word.
"""

from langchain.chat_models import init_chat_model
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from shared import MODEL, run_demo

model = init_chat_model(MODEL)

# NEW: a prompt template. {curly} names are variables, filled in when the chain runs.
# REMOVED: SYSTEM_PROMPT and the hand-built list of SystemMessage / HumanMessage.
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are Barista Bot, the support assistant of {shop_name}, an online shop in India "
            "that sells coffee beans, grinders and brewers.\n"
            "Tone: {tone}.\n"
            "Answer in at most three short sentences. "
            "If you don't know something about the shop, such as an order, say so. Never guess.",
        ),
        ("human", "{question}"),
    ]
)

# NEW: a chain. The | operator ("pipe") sends each part's output into the next part:
#   dict of variables -> prompt -> list of messages -> model -> AIMessage -> parser -> str
chain = prompt | model | StrOutputParser()

# NEW: values that stay the same for every question.
SHOP = {"shop_name": "Bean Street Coffee", "tone": "warm, upbeat and plain-spoken"}


def ask(question: str) -> None:
    # CHANGED: run the chain instead of the model. The input is a dict of the prompt's variables.
    # NEW: .stream() yields the reply in small pieces as the model writes them,
    # instead of .invoke(), which waits for the whole reply.
    print("[barista_bot] ", end="")
    for piece in chain.stream({**SHOP, "question": question}):
        print(piece, end="", flush=True)
    print()


DEMO_PROMPTS = [  # CHANGED: this step's prompts
    "What's the difference between Arabica and Robusta beans?",
    "My grinder makes a squeaking noise. What should I do?",
    "Where is my order BS-1002?",
]

if __name__ == "__main__":
    run_demo(ask, DEMO_PROMPTS)
