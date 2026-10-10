"""Step 01 - Hello, Barista Bot.

Send messages to a chat model and read its reply. Everything else in LangChain builds on this.
"""

from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage, SystemMessage

from shared import MODEL, run_demo

# One line gives you a chat model from any provider. MODEL is "provider:model-name",
# by default "google_genai:gemini-flash-latest" (set in .env, see shared/config.py).
model = init_chat_model(MODEL)

# The system message sets the model's role and rules for the whole conversation.
SYSTEM_PROMPT = (
    "You are Barista Bot, the friendly support assistant of Bean Street Coffee, "
    "an online shop in India that sells coffee beans, grinders and brewers. "
    "Answer in at most three short sentences."
)


def ask(question: str) -> None:
    # A conversation is a list of messages. Each has a role: system, human (the user) or ai.
    messages = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(question),
    ]

    # invoke() sends the whole list to the model and waits for one reply: an AIMessage.
    response = model.invoke(messages)

    # .text is the reply as plain text. (.content can be a list of "content blocks" on newer
    # models, for example text plus reasoning, so prefer .text when you just want the words.)
    print(f"[barista_bot] {response.text}")

    # usage_metadata says how many tokens the call used: what you pay for.
    usage = response.usage_metadata
    print(f"  (tokens: {usage['input_tokens']} in, {usage['output_tokens']} out)")


# The "Try these prompts" from this step's README.
DEMO_PROMPTS = [
    "What's the difference between Arabica and Robusta beans?",
    "How should I store my coffee beans at home?",
    "Where is my order BS-1002?",
]

if __name__ == "__main__":
    run_demo(ask, DEMO_PROMPTS)
