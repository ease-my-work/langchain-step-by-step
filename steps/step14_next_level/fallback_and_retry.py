"""Step 14 example - Model fallback and retries.

The primary model name below is deliberately wrong, so every call to it fails.
ModelFallbackMiddleware then switches to a backup model, and the user still gets an answer.
ModelRetryMiddleware retries calls that fail for a passing reason, such as a timeout or rate limit.

    python steps/step14_next_level/fallback_and_retry.py
"""

from langchain.agents import create_agent
from langchain.agents.middleware import (
    ModelFallbackMiddleware,
    ModelRetryMiddleware,
    wrap_model_call,
)

from shared import MODEL, print_updates, run_demo


# Prints every attempt, so you can see the retry and the fallback happen.
@wrap_model_call
def show_attempts(request, handler):
    name = getattr(request.model, "model", type(request.model).__name__)
    try:
        response = handler(request)
    except Exception as error:
        print(f"[middleware] {name} failed: {type(error).__name__}")
        raise
    print(f"[middleware] {name} answered")
    return response


agent = create_agent(
    model="google_genai:gemini-model-that-does-not-exist",  # fails on every call
    tools=[],
    system_prompt="You are Barista Bot, the support assistant of Bean Street Coffee. Be brief.",
    middleware=[
        # If a model call fails, try these models instead, in order. Can be another provider.
        ModelFallbackMiddleware(MODEL),
        # Retry a call that failed for a passing reason (a timeout, a rate limit) up to twice,
        # waiting longer each time. It doesn't retry errors that can't pass, like a wrong model
        # name, so here the fallback takes over straight away.
        ModelRetryMiddleware(max_retries=2, initial_delay=1.0, on_failure="error"),
        show_attempts,  # innermost, so it sees each attempt with the model actually used
    ],
)


def ask(question: str) -> None:
    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": question}]}, stream_mode="updates"
    ):
        print_updates(chunk)


if __name__ == "__main__":
    run_demo(ask, ["How should I store coffee beans?"])
