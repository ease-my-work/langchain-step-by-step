"""Boilerplate: runs a step's demo prompts and prints what happens in a readable way.

You don't need to read this file to follow the course. Every step's `app.py` ends with
`run_demo(ask, DEMO_PROMPTS)`, which works like this:

    python steps/step01_hello/app.py                    # sends the step's demo prompts
    python steps/step01_hello/app.py "How do I store beans?"   # sends your own message
    python steps/step01_hello/app.py --chat             # chat until you type "exit"
"""

import sys
from collections.abc import Callable, Sequence
from typing import Any

from langchain.messages import AIMessage, ToolMessage

MAX_TOOL_OUTPUT = 300  # Long tool results are shortened when printed (not when sent to the model).

_authors: dict[tuple, str] = {}  # sub-agent namespace -> agent name, for print_updates()


def run_demo(ask: Callable[..., Any], prompts: Sequence[Any], *, all_at_once: bool = False) -> None:
    """Sends the demo prompts, the message on the command line, or a chat, to `ask`.

    A prompt can be a plain string, or a tuple whose first item is the message and whose other
    items are extra arguments for `ask`, such as a customer id: ("Where is my order?", "C-001").
    With all_at_once=True, `ask` gets the whole list in one call (step 04 uses `.batch()`).
    """
    # Print ₹ and other symbols even when Windows sends the output to a file or pipe.
    sys.stdout.reconfigure(encoding="utf-8")

    args = sys.argv[1:]
    if args == ["--chat"]:
        _chat(ask)
        return
    if args:
        prompts = [" ".join(args)]

    if all_at_once:
        ask(list(prompts))
        return
    for prompt in prompts:
        message, *extra = prompt if isinstance(prompt, tuple) else (prompt,)
        label = f"user ({', '.join(map(str, extra))})" if extra else "user"
        print(f"\n[{label}] {message}")
        ask(message, *extra)


def _chat(ask: Callable[..., Any]) -> None:
    print('Chat with Barista Bot. Type "exit" or press Enter on an empty line to stop.')
    while True:
        try:
            message = input("\n[user] ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if message.lower() in ("", "exit", "quit"):
            break
        ask(message)


def print_message(message: Any, author: str = "barista_bot") -> None:
    """Prints a model reply, its tool calls, or a tool result. User messages are skipped."""
    if isinstance(message, AIMessage):
        for call in message.tool_calls:
            print(f"[{author}] -> calls {call['name']}({call['args']})")
        if message.text:
            print(f"[{author}] {message.text.strip()}")
    elif isinstance(message, ToolMessage):
        content = str(message.content)
        if len(content) > MAX_TOOL_OUTPUT:
            content = content[:MAX_TOOL_OUTPUT] + " ..."
        print(f"[{author}] <- {message.name} returned {content}")


def print_updates(chunk: Any, author: str = "barista_bot") -> None:
    """Prints one chunk from `agent.stream(..., stream_mode="updates")`.

    Each chunk is {node_name: update}. The agent's two main nodes are "model" (the model replied)
    and "tools" (tools ran). Middleware adds nodes of its own, such as
    "SummarizationMiddleware.before_model"; when one changes the messages, it gets one line.
    With `subgraphs=True` (step 13), each chunk is a (namespace, {node_name: update}) pair. An empty
    namespace means the main agent; any other is a sub-agent, labelled with the agent's `name`.
    """
    namespace = ()
    if isinstance(chunk, tuple):
        namespace, chunk = chunk
    author = _authors.get(namespace, author)

    for node, update in chunk.items():
        if node == "__interrupt__":
            print(f"[{author}] ⏸ paused, waiting for a human decision")
            continue
        messages = (update or {}).get("messages", [])
        if node in ("model", "tools"):
            for message in messages:
                # A named agent (create_agent(name=...)) puts its name on its replies.
                if namespace and isinstance(message, AIMessage) and message.name:
                    author = _authors[namespace] = message.name
                print_message(message, author)
        elif messages:  # middleware that changed the conversation, e.g. redacted or summarised it
            print(f"[{author}] · {node} changed the messages")
