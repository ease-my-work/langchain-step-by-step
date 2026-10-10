# Step 05 · First tool

> **You'll learn:** how a model calls your Python code. You write the tool loop by hand once, so you know exactly what an agent does for you in step 06.
> **Time:** about 15 minutes · **Previous:** [Step 04 · Composing chains](../step04_compose_chains/) · **Next:** [Step 06 · First agent](../step06_first_agent/)

## What changed

Back to chatting with customers. Barista Bot can now look up real orders (well, fake ones in
[`shared/shop.py`](../../shared/shop.py)).

| Added | Changed | Removed |
| --- | --- | --- |
| `get_order_status(order_id)`, decorated with `@tool` | `ask()` builds the message list by hand again, as in step 01 | The triage, language and reply chains from step 04 |
| `model_with_tools = model.bind_tools([...])` | `SYSTEM_PROMPT` says when to use the tool and "only state order details that a tool gave you" | `.batch()` and `all_at_once` |
| The tool loop: a `while True` in `ask()` | `ask()` prints with `print_message()` (from `shared/`) | |

```bash
git diff --no-index steps/step01_hello/app.py steps/step05_first_tool/app.py
```

(Compare with step 01: step 05 is step 01 plus a tool.)

## Why

Steps 01–04 kept hitting the same wall: "Where is my order BS-1002?" The model can't know; it can only
guess or apologise. **Tools** fix that. You write a function, describe it to the model, and the model can
ask for it to be called. Your code runs it and sends the result back.

## Key concepts

- **Tool.** A function plus a description (name, parameters and their types, docstring) the model reads.
  `@tool` builds that description from your function.
- **`bind_tools([...])`.** Sends the tool descriptions with every request. The model can then reply with
  `tool_calls` instead of, or as well as, text.
- **The model never runs code.** It writes a request, `{"name": "get_order_status", "args": {"order_id":
  "BS-1002"}, "id": "..."}`. You run the function and add the result to the conversation as a
  `ToolMessage`, linked by that `id`.
- **The tool loop.** Call the model; if it asked for tools, run them, add the results, and call the model
  again; stop when it answers without asking:

  ```text
  [system, human]                               -> model -> AIMessage(tool_calls=[get_order_status BS-1002])
  [system, human, ai(tool call), tool(result)]  -> model -> AIMessage("Your order has shipped ...")
  ```

- **Return errors, don't raise them.** For expected problems ("no such order"), return a message the
  model can read and act on. An exception would stop the whole loop.

## Key code

```python
@tool
def get_order_status(order_id: str) -> dict:
    """Look up the status of a Bean Street Coffee order.

    Args:
        order_id: The order number, like "BS-1002".
    """
    order = ORDERS.get(order_id.strip().upper())
    if order is None:
        return {"error": f"No order {order_id}. Order numbers look like BS-1002."}
    ...


model_with_tools = model.bind_tools([get_order_status])

while True:
    response = model_with_tools.invoke(messages)
    messages.append(response)
    if not response.tool_calls:
        break
    for tool_call in response.tool_calls:
        messages.append(get_order_status.invoke(tool_call))
```

| Part | What it does |
| --- | --- |
| `@tool` | Makes a `BaseTool`. Its name is the function name; its description is the docstring; its argument schema comes from the type hints. |
| The docstring | Sent to the model word for word. The `Args:` section explains each parameter, with an example of a good value. |
| `order_id.strip().upper()` | Models write values in many forms ("bs-1002 "). Normalise inputs. |
| `return {"error": ...}` | The model reads this and tells the customer, or tries again. |
| `model.bind_tools([...])` | A new model object that always sends the tool descriptions. |
| `response.tool_calls` | A list of `{"name", "args", "id"}` dicts. Empty when the model just answers. |
| `messages.append(response)` | The model must see its own request in the history, followed by the result. |
| `get_order_status.invoke(tool_call)` | Invoking a tool with a whole tool call returns a `ToolMessage` that carries the call's `id`. (Invoking it with just `tool_call["args"]` would return the plain dict.) |

## Run it

```bash
python steps/step05_first_tool/app.py
```

Lines with `->` are tool calls the model asked for; lines with `<-` are what your function returned.

## Try these prompts

1. `Where is my order BS-1002?` One tool call, then a real answer: shipped with BlueDart, tracking
   BD7731002, due 12 October.
2. `Has BS-1003 shipped yet? And what about BS-1001?` **Two tool calls in one reply.** The model asks for
   both at once (parallel tool calls), your loop runs both, and one answer covers both orders.
3. `What's happening with order BS-9999?` The tool returns an error; the model passes it on politely.
4. `Do you have the Coorg Arabica beans in stock?` **The limit:** there's no stock tool, so the model can't
   check, and tells you to look at the website. Step 06 adds catalogue tools, and lets an agent run the loop.

## Look at the output

```text
[user] Has BS-1003 shipped yet? And what about BS-1001?
[barista_bot] -> calls get_order_status({'order_id': 'BS-1003'})
[barista_bot] -> calls get_order_status({'order_id': 'BS-1001'})
[barista_bot] <- get_order_status returned {"order_id": "BS-1003", ..., "status": "processing", ...}
[barista_bot] <- get_order_status returned {"order_id": "BS-1001", ..., "status": "delivered", ...}
[barista_bot] Order BS-1003 has not shipped yet and is currently processing ... BS-1001 was already delivered on 2026-10-06.
```

The tool returned a `dict`; LangChain turned it into JSON text for the `ToolMessage`, because models read text.

## Break it

> **Press Ctrl+C to stop this one.** It loops forever.

In the loop, delete `messages.append(response)` (or replace it with `pass`) and run
`python steps/step05_first_tool/app.py "Where is my order BS-1002?"`.

The model asks for `get_order_status`, you run it and append the result, and the model asks for it
**again**, and again: it never sees its own request in the history, so a result arriving out of nowhere
doesn't answer anything. Two lessons: the history must hold the request *and* the result, and a tool loop
needs a limit. Step 06's agent manages the history for you, and step 11 adds a call limit.

## Recap

- `@tool` turns a function into a tool; the name, type hints and docstring are what the model sees.
- `bind_tools` lets the model ask for tool calls; it never runs code itself.
- The tool loop: call the model, run the requested tools, append the `ToolMessage`s, repeat until no
  tool calls.
- Return expected errors as data so the model can recover.

## Learn more

- [Tools](https://docs.langchain.com/oss/python/langchain/tools)
- [Models: tool calling](https://docs.langchain.com/oss/python/langchain/models#tool-calling)
