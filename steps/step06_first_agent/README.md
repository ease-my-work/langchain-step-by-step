# Step 06 · First agent

> **You'll learn:** `create_agent`, which runs step 05's tool loop for you, and how an agent chains tool calls on its own.
> **Time:** about 15 minutes · **Previous:** [Step 05 · First tool](../step05_first_tool/) · **Next:** [Step 07 · Memory](../step07_memory/)

## What changed

| Added | Changed | Removed |
| --- | --- | --- |
| `search_products(query)`: keyword search of the catalogue | `SYSTEM_PROMPT`: ROLE / RULES / TOOLS / FORMAT sections, for three tools | `model.bind_tools(...)` |
| `check_stock(product_id)`: stock and notes for one product | `ask()` streams the agent with `stream_mode="updates"` | The hand-written `while True` tool loop |
| `agent = create_agent(model, tools, system_prompt)` | Messages are written as `{"role": ..., "content": ...}` dicts | `SystemMessage` / `HumanMessage` imports |

```bash
git diff --no-index steps/step05_first_tool/app.py steps/step06_first_agent/app.py
```

## Why

Step 05's loop works, but you'd write it again for every app, and add a call limit, error handling,
streaming, memory, a human check... `create_agent` is that loop, done once and done well, with places to
plug all those things in (steps 07–13). With several tools, the model also has to plan: to answer "is the
Coorg Arabica in stock?" it must **search** for the product id, then **check stock** with it.

## Key concepts

- **Agent.** A model in a loop with tools: it decides which tool to call, looks at the result, and
  decides again, until it can answer. You give it a goal (the user's message), not a list of steps.
- **`create_agent(model, tools, system_prompt=...)`.** Builds the agent. It returns a runnable (a
  LangGraph graph) with `invoke`, `stream` and `batch`, like the chains in Part 1.
- **Agent input and output.** The input is `{"messages": [...]}`; the output is the same dict, with every
  message the run added: tool calls, tool results and the final answer.
- **Streaming updates.** `agent.stream(..., stream_mode="updates")` yields one chunk each time a step of
  the loop finishes: `{"model": {...}}` when the model replied, `{"tools": {...}}` when tools ran.
- **Tools that feed tools.** `search_products` returns ids; `check_stock` needs one. The docstrings say
  so, and the model works out the order.

## Key code

```python
agent = create_agent(
    model=model,
    tools=[get_order_status, search_products, check_stock],
    system_prompt=SYSTEM_PROMPT,
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": question}]},
    stream_mode="updates",
):
    print_updates(chunk)
```

| Part | What it does |
| --- | --- |
| `model=model` | Any chat model, or a `"provider:model"` string. |
| `tools=[...]` | Plain `@tool` functions. The agent binds them to the model for you. |
| `system_prompt=...` | Added as the system message on every model call. |
| `{"role": "user", "content": question}` | A message as a dict. Same as `HumanMessage(question)`. |
| `stream_mode="updates"` | One chunk per finished step. `agent.invoke(...)` would return only the final state. |
| `print_updates(chunk)` | From `shared/console.py`: prints `->` tool calls, `<-` results and replies, like step 05. |

> **Want just the answer?** `result = agent.invoke({"messages": [...]})`, then `result["messages"][-1].text`.

## Run it

```bash
python steps/step06_first_agent/app.py
python steps/step06_first_agent/app.py "Which grinder would you suggest for espresso, and is it in stock?"
```

## Try these prompts

1. `Where is my order BS-1002?` One tool call, as in step 05, without the hand-written loop.
2. `Do you have the Coorg Arabica beans in stock?` **Two tools in sequence:** `search_products("Coorg")`
   finds `BEAN-CRG`, then `check_stock("BEAN-CRG")` says 0, back on 20 October. You wrote no code for that order.
3. `I want a decaf for cold brew. What do you have, and is it in stock?` The same plan for a vaguer question.
4. `Can you recommend a good laptop?` The RULES section makes it decline politely. No tools called.
5. `I loved my last order. Can you send me the same again?` **The limit:** the agent doesn't know who you
   are or what you ordered, so it asks for an order number. And if you told it your name in one message, it
   would forget by the next: each `ask()` starts from nothing. Step 07 adds memory; step 08, who's logged in.

## Look at the output

```text
[user] Do you have the Coorg Arabica beans in stock?
[barista_bot] -> calls search_products({'query': 'Coorg'})
[barista_bot] <- search_products returned [{"product_id": "BEAN-CRG", "name": "Coorg Estate Arabica beans, 250 g", "price_inr": 720}]
[barista_bot] -> calls check_stock({'product_id': 'BEAN-CRG'})
[barista_bot] <- check_stock returned {"product_id": "BEAN-CRG", "in_stock": 0, "notes": "... Back in stock on 20 October."}
[barista_bot] The Coorg Estate Arabica beans (250 g, ₹720) are currently out of stock. They are expected to be back in stock on 20 October. ...
```

Three model calls and two tool runs for one question: each `->` line is one model call asking for a
tool, and the last line is the final model call.

> **Optional: see it as a trace.** Set the three `LANGSMITH_*` lines in `.env` (free account at
> [smith.langchain.com](https://smith.langchain.com)) and run again. Every run then shows up in LangSmith
> as a tree: each model call with its exact prompt and token count, each tool call with its input and
> output. No code change needed.

## Break it

Take `check_stock` out of the agent's `tools` list (leave it in the TOOLS section of the prompt) and ask
prompt 2 again. The agent still finds the product with `search_products`, then says it is "unable to check
live stock levels". A tool mentioned in the prompt doesn't exist for the model; only tools passed in
`tools=[...]` are sent to it. The prompt says *when* to use a tool; the `tools` list decides *which* tools
exist.

> **Try this too.** Rename `check_stock`'s parameter from `product_id` to `pid` and delete its docstring's
> `Args:` section. When we tried it, Gemini still called the tools in the right order: a clear tool name and
> the ids from `search_products` were enough. Docstrings matter most for what names can't say: units,
> formats, and which tool's output feeds which input.

## Recap

- `create_agent(model, tools, system_prompt)` runs the model → tools → model loop until a final answer.
- Input and output are `{"messages": [...]}`; `stream_mode="updates"` shows each step as it happens.
- With several tools, the model plans the order itself; clear docstrings make that work.

## Learn more

- [Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [Streaming](https://docs.langchain.com/oss/python/langchain/streaming)
- [LangSmith observability](https://docs.langchain.com/oss/python/langchain/observability)
