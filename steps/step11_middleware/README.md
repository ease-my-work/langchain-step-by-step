# Step 11 · Middleware

> **You'll learn:** what middleware is, how to add LangChain's built-in middleware (PII redaction, call limits, summarisation), and how to write your own hooks.
> **Time:** about 20 minutes · **Previous:** [Step 10 · RAG agent](../step10_rag_agent/) · **Next:** [Step 12 · Human in the loop](../step12_human_in_the_loop/)

## What changed

| Added | Changed | Removed |
| --- | --- | --- |
| `PIIMiddleware("credit_card", strategy="mask")` and `PIIMiddleware("email", strategy="redact")` | `middleware=[...]` grows from one item to seven | |
| `ModelCallLimitMiddleware(run_limit=6)` | `ask()` prints how many messages the thread holds | |
| `SummarizationMiddleware(trigger=("messages", 12), keep=("messages", 4))` | `search_handbook` moved to [`knowledge.py`](knowledge.py), unchanged | |
| `show_what_model_sees`: a custom `@before_model` hook | Demo: one long chat with Asha | |
| `log_tool_calls`: a custom `@wrap_tool_call` hook | | |

```bash
git diff --no-index steps/step10_rag_agent/app.py steps/step11_middleware/app.py
```

## Why

Step 10's prompt has a lot of rules, and a prompt is a request, not a guarantee. Some things must happen
**every time**, in code:

- a card number must never reach the model, the logs or the database;
- a confused model must not loop forever (remember step 05's Break it);
- a long chat must not grow until it's slow, expensive or over the model's limit.

Middleware is code that runs around the agent's loop, so it can enforce these on every call.

## Key concepts

- **Middleware.** An object or decorated function passed in `create_agent(middleware=[...])`. It can hook
  into these points of the loop:

  ```text
  before_agent
    ┌─> before_model -> wrap_model_call( model ) -> after_model ─┐
    │                                                            │ tool calls?
    └──────────────── wrap_tool_call( tool ) <───────────────────┘
  after_agent
  ```

  `before_*` / `after_*` hooks see the state and can change it. `wrap_*` hooks get a `handler` to call the
  model or tool themselves: run code before, after, instead, or several times (retries, caching).
- **Order matters.** `before_*` hooks run in list order; `after_*` hooks run in reverse; the first `wrap_*`
  middleware is the outermost.
- **Built-in middleware** used here:

  | Middleware | What it does here |
  | --- | --- |
  | `PIIMiddleware("credit_card", strategy="mask")` | Rewrites card numbers in user messages before the model sees them: `**** **** **** 1111`. The checkpointer saves the masked version. |
  | `PIIMiddleware("email", strategy="redact")` | Replaces email addresses with `[REDACTED_EMAIL]`. Other strategies: `block` (raise an error), `hash`. Custom types take a regex `detector`. |
  | `ModelCallLimitMiddleware(run_limit=6, exit_behavior="end")` | Ends a run after 6 model calls. `thread_limit` caps a whole conversation. |
  | `SummarizationMiddleware(model, trigger=("messages", 12), keep=("messages", 4))` | When the thread passes 12 messages, a model call summarises the older ones and replaces them; the last 4 stay as they are. |

  There are more: `HumanInTheLoopMiddleware` (step 12), `ModelFallbackMiddleware` and
  `ModelRetryMiddleware` (step 14), `ToolCallLimitMiddleware`, `LLMToolSelectorMiddleware`,
  `TodoListMiddleware` and others.
- **Your own middleware.** `@before_model`, `@after_model`, `@wrap_model_call`, `@wrap_tool_call`,
  `@before_agent`, `@after_agent`, and step 08's `@dynamic_prompt`. For several hooks with shared settings,
  subclass `AgentMiddleware`.

## Key code

```python
@before_model
def show_what_model_sees(state: AgentState, runtime: Runtime) -> None:
    last_user_message = next(m for m in reversed(state["messages"]) if m.type == "human")
    print(f"[middleware] model sees: {last_user_message.text}")


@wrap_tool_call
def log_tool_calls(request, handler):
    started = time.perf_counter()
    result = handler(request)  # runs the tool
    print(f"[middleware] {request.tool_call['name']} took ...")
    return result


agent = create_agent(
    ...,
    middleware=[
        personalised_prompt,
        PIIMiddleware("credit_card", strategy="mask"),
        PIIMiddleware("email", strategy="redact"),
        ModelCallLimitMiddleware(run_limit=6, exit_behavior="end"),
        SummarizationMiddleware(model=model, trigger=("messages", 12), keep=("messages", 4)),
        show_what_model_sees,
        log_tool_calls,
    ],
)
```

| Part | What it does |
| --- | --- |
| `@before_model` | Runs before every model call with the current state. Return `None` to change nothing, or a dict of state updates, such as `{"messages": [...]}`. |
| `show_what_model_sees` placed after the PII middleware | It runs after them, so it prints the redacted text (see Break it). |
| `@wrap_tool_call` | `request.tool_call` is the call; `handler(request)` runs the tool and returns its `ToolMessage`. |
| `SummarizationMiddleware(model=model, ...)` | Needs a model to write the summary. Often a cheaper one than the agent's. |

## Run it

```bash
python steps/step11_middleware/app.py
```

The demo is one chat with Asha, five messages long, so you can watch the thread grow and shrink.

## Try these prompts

1. `My card 4111 1111 1111 1111 was charged twice for order BS-1002! Email the receipt to asha.r@example.com`
   The two PII lines fire, and the model sees
   `My card **** **** **** 1111 ... Email the receipt to [REDACTED_EMAIL]`. It still answers usefully
   (it knows the last four digits) without ever seeing the full number.
2. `What does the warranty on that grinder cover?` The thread reaches 11 messages.
3. `And how long do its burrs last?` The thread passes 12, so `SummarizationMiddleware` fires
   **before** the model call, and the count drops to 6: one summary, the last few messages, and this turn.
4. `Is the decaf in stock?` Two tools, timed by `log_tool_calls`.
5. `What did I first contact you about today?` The original messages are gone, but the summary kept the
   gist: the double charge on order BS-1002, the card ending 1111, the receipt request.

**The limit:** Barista Bot can find out a refund is due, but it can't issue one, and you wouldn't want an
AI to move money on its own anyway. Step 12 adds a refund tool that waits for a human's approval.

## Look at the output

```text
[barista_bot] · PIIMiddleware[credit_card].before_model changed the messages
[barista_bot] · PIIMiddleware[email].before_model changed the messages
[middleware] model sees: My card **** **** **** 1111 was charged twice for order BS-1002! Email the receipt to [REDACTED_EMAIL]
...
  (thread 'C-001' now holds 11 messages)

[user] And how long do its burrs last?
[barista_bot] · SummarizationMiddleware.before_model changed the messages
...
  (thread 'C-001' now holds 6 messages)
```

Each `·` line is a built-in middleware that changed the conversation; its node name tells you which hook
did it. In LangSmith (step 06's tip), each middleware appears as its own step in the trace.

## Break it

Move `show_what_model_sees` to the top of the list, before the PII middleware, and run prompt 1 with
`python steps/step11_middleware/app.py "My card 4111 1111 1111 1111 was charged twice for order BS-1002"`.
It now prints the **full card number**. The model still gets the masked text (the PII middleware runs
afterwards), but your hook saw the raw data first. If that hook were a logger, you'd have just written card
numbers to your logs. Put redaction first.

## Recap

- Middleware hooks into the agent loop: before/after the model, around model and tool calls, before/after the run.
- Built-ins cover common needs: PII redaction, call limits, summarisation, fallbacks, retries, human approval.
- Write your own with `@before_model`, `@wrap_tool_call` and friends.
- Order matters: `before_*` hooks run in list order.

## Learn more

- [Middleware overview](https://docs.langchain.com/oss/python/langchain/middleware)
- [Prebuilt middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in)
- [Custom middleware](https://docs.langchain.com/oss/python/langchain/middleware/custom)
- [Guardrails](https://docs.langchain.com/oss/python/langchain/guardrails)
