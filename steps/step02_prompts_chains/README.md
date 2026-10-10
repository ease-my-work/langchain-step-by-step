# Step 02 · Prompts and chains

> **You'll learn:** prompt templates with variables, joining parts into a chain with `|`, and streaming the reply as it is written.
> **Time:** about 10 minutes · **Previous:** [Step 01 · Hello, Barista Bot](../step01_hello/) · **Next:** [Step 03 · Structured output](../step03_structured_output/)

## What changed

| Added | Changed | Removed |
| --- | --- | --- |
| `prompt`: a `ChatPromptTemplate` with `{shop_name}`, `{tone}` and `{question}` | `ask()` runs the chain, not the model | `SYSTEM_PROMPT` and the hand-built `SystemMessage` / `HumanMessage` list |
| `chain = prompt \| model \| StrOutputParser()` | `ask()` uses `.stream()` instead of `.invoke()` | Token counts (a `str` has no `usage_metadata`) |
| `SHOP`: values that are the same for every question | The system prompt now says "If you don't know something about the shop, say so. Never guess." | |

See it as a diff:

```bash
git diff --no-index steps/step01_hello/app.py steps/step02_prompts_chains/app.py
```

## Why

In step 01 the prompt was one fixed string, built by hand into a list of messages, and you waited for
the whole reply. Real apps fill prompts with data (the shop's name, the customer's question, later the
customer's tier), and users don't like staring at a blank screen. Templates handle the first, streaming
the second, and chains let you join the parts together once and reuse them.

## Key concepts

- **Prompt template.** A prompt with `{placeholders}`. `ChatPromptTemplate.from_messages([...])` takes
  `(role, text)` pairs and, when it runs, returns the list of messages with the blanks filled in.
- **Runnable.** Anything in LangChain you can `invoke()`, `stream()` or `batch()`: models, prompts,
  output parsers, chains, and (from step 06) agents. They all share these methods.
- **Chain (LCEL).** `a | b | c` makes a new runnable that sends `a`'s output into `b`, and `b`'s into `c`.
  This is the **LangChain Expression Language**. Here:

  ```text
  {"shop_name": ..., "tone": ..., "question": ...}
     -> prompt            -> [SystemMessage, HumanMessage]
     -> model             -> AIMessage
     -> StrOutputParser() -> "plain text"
  ```

- **Output parser.** Turns a model's `AIMessage` into something handier. `StrOutputParser` returns its text.
- **Streaming.** `.stream()` yields the output in small pieces as the model writes them. Every part of a
  chain supports it, so the parser passes text pieces through as soon as the model produces them.

## Key code

```python
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are Barista Bot, the support assistant of {shop_name}, ...\nTone: {tone}. ...",
        ),
        ("human", "{question}"),
    ]
)
chain = prompt | model | StrOutputParser()

for piece in chain.stream({**SHOP, "question": question}):
    print(piece, end="", flush=True)
```

| Part | What it does |
| --- | --- |
| `("system", "...{shop_name}...")` | A message template. The role comes first, then text with placeholders. |
| `("human", "{question}")` | The user's message, filled in per call. |
| `prompt \| model \| StrOutputParser()` | Builds the chain. Nothing runs yet; this only describes the steps. |
| `{**SHOP, "question": question}` | The chain's input: a dict with a value for every placeholder. |
| `chain.stream(...)` | Runs the chain and yields text pieces as they arrive. `chain.invoke(...)` would return the full string at once. |
| `print(..., end="", flush=True)` | Prints each piece on the same line, straight away. |

## Run it

```bash
python steps/step02_prompts_chains/app.py
```

Watch the answers appear a few words at a time. Your own message: `python steps/step02_prompts_chains/app.py "Is your coffee organic?"`.

## Try these prompts

1. `What's the difference between Arabica and Robusta beans?` Same question as step 01, now streamed and
   in the tone from `SHOP`.
2. `My grinder makes a squeaking noise. What should I do?` General advice, and a nudge to contact the shop.
3. `Where is my order BS-1002?` It now says it can't check orders instead of asking for your phone number.
   That's the new "Never guess" rule. But when we ran it, it invented a support email address
   (`support@beanstreetcoffee.in`). **This is the limit:** rules in a prompt reduce guessing, they don't
   stop it. Only tools (step 05) and documents (step 10) give the model real facts.

Then change `SHOP["tone"]` to `"formal and very brief"` or `"like a pirate"` and run again. One value changes
every answer, and no prompt text was touched.

## Look at the output

The reply prints in bursts rather than all at once. Each burst is one piece from `.stream()`. Gemini sends
fairly large pieces; other providers send a few characters at a time.

## Break it

In `ask()`, leave out the shop values:

```python
for piece in chain.stream({"question": question}):
```

You get a `KeyError` that names exactly what's missing: the prompt needs `shop_name` and `tone`. A
template checks its inputs before anything is sent to the model, so a typo in a variable name fails fast
instead of sending a prompt with a hole in it.

## Recap

- `ChatPromptTemplate` builds messages from `(role, text)` pairs with `{placeholders}`.
- `prompt | model | parser` is a chain. Every part, and the chain itself, is a runnable with `invoke`,
  `stream` and `batch`.
- `.stream()` yields the answer piece by piece. Use it whenever a person is waiting.

## Learn more

- [Streaming](https://docs.langchain.com/oss/python/langchain/streaming)
- [`ChatPromptTemplate` reference](https://reference.langchain.com/python/langchain-core/prompts/chat/ChatPromptTemplate)
- [Runnables reference](https://reference.langchain.com/python/langchain-core/runnables)
