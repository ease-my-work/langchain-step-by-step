"""Barista Bot's built-in middleware from step 11 (unchanged).

It moved here to keep app.py about what is new in this step. Step 11's two custom hooks,
show_what_model_sees and log_tool_calls, were only there to show how hooks work, so they are gone.
"""

from langchain.agents.middleware import (
    ModelCallLimitMiddleware,
    PIIMiddleware,
    SummarizationMiddleware,
)
from langchain.chat_models import BaseChatModel


def guardrails(model: BaseChatModel) -> list:
    """Step 11's middleware list. SummarizationMiddleware needs a model to write its summaries."""
    return [
        PIIMiddleware("credit_card", strategy="mask"),
        PIIMiddleware("email", strategy="redact"),
        ModelCallLimitMiddleware(run_limit=6, exit_behavior="end"),
        SummarizationMiddleware(model=model, trigger=("messages", 12), keep=("messages", 4)),
    ]
