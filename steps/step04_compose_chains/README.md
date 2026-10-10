# Step 04 · Composing chains

> **You'll learn:** how to join small chains into a pipeline: run chains in parallel, pick the next chain in code, and process many inputs at once.
> **Time:** about 15 minutes · **Previous:** [Step 03 · Structured output](../step03_structured_output/) · **Next:** [Step 05 · First tool](../step05_first_tool/)

## What changed

Barista Bot now works through the whole inbox: it triages each email, notices its language, and drafts a
reply, choosing a different reply for urgent emails.

| Added | Changed | Removed |
| --- | --- | --- |
| `language_chain`: names the email's language | `chain` renamed `triage_chain` (otherwise as in step 03) | Printing the full ticket as JSON |
| `reply_chain` and `escalation_chain`: two ways to reply | `ask()` gets the whole inbox at once and uses `.batch()` | |
| `choose_reply()`: routing in plain Python | Demo prompts: three emails, one in Hinglish | |
| `pipeline`: `RunnableParallel` → `RunnablePassthrough.assign` → `RunnableLambda` | `run_demo(..., all_at_once=True)` | |

```bash
git diff --no-index steps/step03_structured_output/app.py steps/step04_compose_chains/app.py
```

## Why

Real tasks are more than one prompt. Triage, language detection and reply-writing are separate jobs:
each is easier to write, test and improve as its own small chain. LCEL lets you join them so the
whole pipeline is still one runnable, with `invoke`, `stream` and `batch`, and LangChain runs independent
parts at the same time for you.

This is a **fixed process**: you decide the steps and the order. From step 05 on, an *agent* decides the
steps itself. Use a chain when you know the steps, and an agent when you don't.

## Key concepts

- **`RunnableParallel(a=..., b=...)`.** Runs every part on the same input at the same time and returns
  `{"a": ..., "b": ...}`. Triage and language detection don't depend on each other, so they run together.
- **`RunnablePassthrough.assign(key=...)`.** Passes its input dict through and adds one more key,
  computed from that input. Handy for "keep everything so far, plus this".
- **`RunnableLambda(function)`.** Makes a plain Python function part of a chain. **If the function
  returns a runnable, LangChain runs that runnable** with the same input. That's routing.
- **`.batch(inputs)`.** Runs the chain on a list of inputs, several at once, and returns the outputs in
  the same order.
- **Plain functions are welcome.** `itemgetter("email")` is ordinary Python; inside `RunnableParallel`,
  LangChain wraps it in a `RunnableLambda` for you.

## Key code

```python
def choose_reply(inputs: dict):
    if inputs["ticket"].priority == "urgent":
        return escalation_chain
    return reply_chain


pipeline = RunnableParallel(
    email=itemgetter("email"),
    ticket=triage_chain,
    language=language_chain,
) | RunnablePassthrough.assign(reply=RunnableLambda(choose_reply))

results = pipeline.batch([{"email": email} for email in emails])
```

The data flowing through, for one email:

```text
{"email": "..."}
  -> RunnableParallel      -> {"email": "...", "ticket": Ticket(...), "language": "Hindi"}
  -> assign(reply=...)     -> {"email": ..., "ticket": ..., "language": ..., "reply": "नमस्ते! ..."}
```

| Part | What it does |
| --- | --- |
| `email=itemgetter("email")` | Keeps the email text in the result, for the reply prompts and for printing. |
| `ticket=triage_chain`, `language=language_chain` | Two model calls, made at the same time. |
| `choose_reply(inputs)` | Ordinary `if`. Returns a chain; it doesn't call it. |
| `RunnablePassthrough.assign(reply=...)` | Runs the chosen chain with the whole dict (it needs `{email}` and `{language}`) and adds `reply`. |
| `pipeline.batch([...])` | One pipeline run per email, several at once. Three emails take about as long as one. |

## Run it

```bash
python steps/step04_compose_chains/app.py
python steps/step04_compose_chains/app.py "Bonjour, ma commande BS-1003 est-elle partie ?"
```

## Try these prompts

The demo sends all three at once, with `.batch()`:

1. `Hi! Ordered an electric grinder last week (BS-1002). ...` `order_status`, English, a normal reply.
2. `This is the second time my beans arrived with a torn bag ... I want my money back NOW.` `urgent`, so
   `choose_reply` picks `escalation_chain`: an apology and "a senior team member will contact you within
   4 hours".
3. `Namaste, kya aapke paas decaf coffee hai jo cold brew ke liye achhi ho?` Hinglish (Hindi in Latin
   letters). The language chain says Hindi, and the reply comes back in Hindi.

**The limit:** every reply says "a human will check the details", because the pipeline can't look up
anything: it doesn't know BS-1002 has shipped or that the decaf is in stock. Step 05 adds tools.

## Look at the output

```text
[email] This is the second time my beans arrived with a torn bag ...
[triage] return_or_refund, urgent, language: English
[reply] I am truly sorry to hear that your order BS-1001 arrived damaged again ... a senior team member
will contact you within 4 hours ...
```

Time it: the three emails take about as long as the slowest one, because `.batch()` and
`RunnableParallel` run things at the same time. (On a free API tier with a tight rate limit, you may see a
pause while the client waits for the limit to reset.)

## Break it

In `ask()`, pass the emails as plain strings:

```python
results = pipeline.batch(emails)
```

It fails with `TypeError: string indices must be integers, not 'str'`: `itemgetter("email")` received a string, not
a dict. Every part of a chain expects a particular input shape, and the first part sets the shape of the
whole chain's input. When a chain fails, check what each part receives.

## Recap

- `RunnableParallel` runs independent parts at the same time and returns a dict.
- `RunnablePassthrough.assign` adds a key to the dict flowing through.
- A function in a chain can return another chain: that's routing in code.
- `.batch()` processes many inputs at once. Chains are for processes whose steps you know in advance.

## Learn more

- [`RunnableParallel` reference](https://reference.langchain.com/python/langchain-core/runnables/base/RunnableParallel)
- [Runnables reference](https://reference.langchain.com/python/langchain-core/runnables)
- For bigger fixed workflows (loops, retries, human approval), LangGraph: see [step 14](../step14_next_level/)
