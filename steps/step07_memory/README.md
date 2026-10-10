# Step 07 · Memory

> **You'll learn:** how a checkpointer gives an agent memory within a conversation, and how thread ids keep conversations apart.
> **Time:** about 10 minutes · **Previous:** [Step 06 · First agent](../step06_first_agent/) · **Next:** [Step 08 · Runtime context](../step08_runtime_context/)

## What changed

| Added | Changed | Removed |
| --- | --- | --- |
| `checkpointer = InMemorySaver()`, passed to `create_agent` | `ask()` takes a `thread_id` and passes `config={"configurable": {"thread_id": ...}}` | |
| `agent.get_state(config)`: prints how many messages a thread holds | The three tools moved to [`shop_tools.py`](shop_tools.py), unchanged | |
| | Demo prompts are `(message, thread id)` pairs: three for Asha, two for Rahul | |

```bash
git diff --no-index steps/step06_first_agent/app.py steps/step07_memory/app.py
```

## Why

In step 06, every `ask()` started from nothing. Tell Barista Bot your name, ask a follow-up, and it has
forgotten. As you saw in step 01, the model itself has no memory: something must send the earlier messages
again on every call. A **checkpointer** does that for you, and keeps each customer's conversation separate.

## Key concepts

- **Checkpointer.** Saves the agent's state (its message list and more) after every step, under a
  **thread id**. On the next run with the same thread id, the agent loads it first, adds your new message,
  and carries on.
- **Thread.** One conversation. Same thread id: same memory. New thread id: a fresh start. In an app,
  that's usually one thread per chat window or support ticket.
- **`config`.** Settings for one run. `{"configurable": {"thread_id": "asha"}}` names the thread.
- **Send only the new message.** The agent adds it to what the checkpointer already holds.
- **`InMemorySaver`** keeps threads in this Python process: gone when the script ends. For production,
  swap in a database-backed checkpointer (`PostgresSaver`, `SqliteSaver`, ...) with no other change.
- **This is short-term memory**: one conversation. Remembering a customer *across* conversations is
  long-term memory; see step 14.

## Key code

```python
checkpointer = InMemorySaver()

agent = create_agent(
    model=model,
    tools=[get_order_status, search_products, check_stock],
    system_prompt=SYSTEM_PROMPT,
    checkpointer=checkpointer,
)

config = {"configurable": {"thread_id": thread_id}}
agent.stream({"messages": [{"role": "user", "content": question}]}, config, stream_mode="updates")

saved = agent.get_state(config).values["messages"]
```

| Part | What it does |
| --- | --- |
| `checkpointer=checkpointer` | Turns memory on. Without it, `thread_id` is ignored. |
| `config` (second argument) | Which thread this message belongs to. |
| `agent.get_state(config)` | Reads the saved state of a thread: `.values["messages"]` is the full conversation. |

## Run it

```bash
python steps/step07_memory/app.py
python steps/step07_memory/app.py --chat
```

In `--chat` mode, every message goes to the same thread, so you can test memory yourself. (The demo
prompts below use two threads.)

## Try these prompts

Asha's thread (`asha`):

1. `Hi, I'm Asha. Where is my order BS-1002?` Looks it up. The thread now holds 4 messages: yours, the
   tool call, the tool result, the answer.
2. `Which courier has it? And remind me, what's my name?` "BlueDart", and "Asha", **with no tool call**:
   both are in the saved conversation.
3. `Is the decaf in stock? I'd like to add it to that order.` "That order" is BS-1002, from turn 1. The
   agent checks stock and points out that a shipped order can't be changed.

Rahul's thread (`rahul`):

4. `What's my name, and which order did I ask about?` It doesn't know: a new thread starts empty. Threads
   don't leak into each other.
5. `Where is order BS-1002?` **The limit:** Rahul gets Asha's order, courier and tracking number. Anyone
   who knows an order number can read it. Barista Bot has no idea who is logged in. Step 08 fixes that.

## Look at the output

```text
[user (asha)] Which courier has it? And remind me, what's my name?
[barista_bot] Your order is being handled by BlueDart. And you introduced yourself as Asha!
  (thread 'asha' now holds 6 messages)
```

The thread grows by 2 messages for a plain answer, and by 2 more for each tool call and its result. All of
them are sent to the model on every turn, which costs tokens; step 11 shows how to summarise long threads.

## Break it

Pass `checkpointer=None` to `create_agent` (or delete that line). The first turn answers, then fails at
`get_state()` with `ValueError: No checkpointer set`: there's no saved state to read. Delete the two
`get_state` lines too and run again: everything works, but turn 2 no longer knows the courier or the name.
The `thread_id` is silently ignored. Memory is the checkpointer, not the thread id.

## Recap

- A checkpointer saves each thread's state after every step; the thread id picks the conversation.
- Pass `config={"configurable": {"thread_id": ...}}` and send only the new message.
- `get_state(config)` shows what is saved. Swap `InMemorySaver` for a database saver in production.

## Learn more

- [Short-term memory](https://docs.langchain.com/oss/python/langchain/short-term-memory)
