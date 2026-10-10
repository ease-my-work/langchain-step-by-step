# LangChain Step by Step

[![CI](https://github.com/ease-my-work/langchain-step-by-step/actions/workflows/ci.yml/badge.svg)](https://github.com/ease-my-work/langchain-step-by-step/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![LangChain 1.4](https://img.shields.io/badge/langchain-1.4-1C3C3C.svg)](https://pypi.org/project/langchain/)

Learn **[LangChain](https://docs.langchain.com/oss/python/langchain/overview)** in about three hours by
building one customer-support assistant, **Barista Bot**, a little at a time.

Barista Bot answers customers of **Bean Street Coffee**, a made-up online shop in India that sells coffee
beans, grinders and brewers. Over 13 steps it learns to write replies, triage emails, look up orders,
remember conversations, know who is logged in, answer from the shop's policy handbook, protect card
numbers, ask a human before refunding money, and hand work to specialist agents.

Each step is a folder with one runnable `app.py`. It has everything the previous step had, plus one or two
new features, and its README tells you exactly what was **added**, **changed** or **removed**, and why.

> **Who is this for?** Python developers who are new to LangChain, or new to LLM apps altogether.
> You need Python 3.10+ and a free Gemini API key. No cloud account, Docker or database.

## Contents

- [What is LangChain?](#what-is-langchain)
- [Setup](#setup)
- [The steps](#the-steps)
- [How to read a step](#how-to-read-a-step)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## What is LangChain?

LangChain is an open-source Python framework for building apps on large language models: from a single
prompt, through chains of model calls, to **agents** that decide which of your functions ("tools") to call
and keep going until the job is done.

It gives you the parts you would otherwise write yourself, with **one interface for every model provider**:

| You need… | LangChain gives you… | First seen in |
| --- | --- | --- |
| A model from any provider | `init_chat_model("provider:model")`, messages | Step 01 |
| Reusable prompts and pipelines | Prompt templates, chains with `\|` (LCEL), streaming, batching | Steps 02, 04 |
| Data, not text, from a model | Structured output with Pydantic | Step 03 |
| The model to call your code | `@tool`, tool calling | Step 05 |
| A model that plans and acts | `create_agent` | Step 06 |
| Memory and per-user data | Checkpointers and threads, runtime context | Steps 07–08 |
| Answers from your documents | Embeddings, vector stores, RAG | Steps 09–10 |
| Guardrails in code | Middleware: PII redaction, limits, summarisation | Step 11 |
| A human "yes" before risky actions | Human-in-the-loop middleware | Step 12 |
| Several agents working together | Sub-agents as tools | Step 13 |

LangChain's agents run on **LangGraph**, its lower-level library for stateful workflows (step 14 shows it).

## Setup

About five minutes. Run every command from the repo root.

**1. Get the code**

```bash
git clone https://github.com/ease-my-work/langchain-step-by-step.git
cd langchain-step-by-step
```

**2. Create a virtual environment and install**

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows (PowerShell):

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

This installs LangChain, the Gemini integration and a small local package, `shared/`, that holds the
course's boilerplate (see [How to read a step](#how-to-read-a-step)).

**3. Add your Gemini API key**

Create a free key at [Google AI Studio](https://aistudio.google.com/apikey), then copy the example file:

```bash
cp .env.example .env      # Windows: copy .env.example .env
```

Open `.env` and replace `paste-your-key-here` with your key. Every step reads this one file. `.env` is
git-ignored: **never commit it**.

Want another provider (OpenAI, Anthropic, a local model with Ollama)? Change `MODEL` in `.env`; see
[step 14](steps/step14_next_level/#1-other-model-providers).

**4. Run the first step**

```bash
python steps/step01_hello/app.py
```

Every step runs the same three ways:

```bash
python steps/step01_hello/app.py                           # sends the step's demo prompts
python steps/step01_hello/app.py "How do I store beans?"   # sends your own message
python steps/step01_hello/app.py --chat                    # chat until you type "exit"
```

> **Cost.** The free Gemini tier is enough for the whole course. Steps 10–13 make several model calls per
> message, so if you hit a rate limit (`429`), wait a minute and try again.

> **Optional: see every step as a trace.** Fill in the `LANGSMITH_*` lines in `.env` (free account at
> [smith.langchain.com](https://smith.langchain.com)) and every run appears in LangSmith, with each model
> call, prompt, tool call and token count. Not needed for the course.

## The steps

13 steps in four parts, plus a tour of what's next. Do them in order the first time: each step builds on
the one before it, and each README starts with what changed since then. Every step runs on its own, so you
can stop after any step and come back later.

### Part 1 · Models, prompts and chains (steps 01–04, about 45 minutes)

The building blocks of every LangChain app. No agent yet.

| # | Step | Barista Bot can now… | LangChain concepts |
| --- | --- | --- | --- |
| 01 | [Hello, Barista Bot](steps/step01_hello/) | Answer a coffee question | `init_chat_model`, messages, `invoke`, `.text`, `usage_metadata` |
| 02 | [Prompts and chains](steps/step02_prompts_chains/) | Reply in the shop's voice, word by word | `ChatPromptTemplate`, LCEL `\|`, `StrOutputParser`, `.stream()` |
| 03 | [Structured output](steps/step03_structured_output/) | Turn an email into a support ticket | `with_structured_output`, Pydantic, `Literal`, `Field` |
| 04 | [Composing chains](steps/step04_compose_chains/) | Triage a whole inbox and draft replies | `RunnableParallel`, `RunnablePassthrough.assign`, `RunnableLambda`, `.batch()` |

### Part 2 · Tools and agents (steps 05–08, about an hour)

Barista Bot gets tools, a loop, memory, and knows who it's talking to.

| # | Step | Barista Bot can now… | LangChain concepts |
| --- | --- | --- | --- |
| 05 | [First tool](steps/step05_first_tool/) | Look up an order | `@tool`, `bind_tools`, `tool_calls`, `ToolMessage`, the tool loop by hand |
| 06 | [First agent](steps/step06_first_agent/) | Search products and check stock on its own | `create_agent`, `system_prompt`, `stream_mode="updates"` |
| 07 | [Memory](steps/step07_memory/) | Remember the conversation; keep customers apart | Checkpointer (`InMemorySaver`), `thread_id`, `get_state` |
| 08 | [Runtime context](steps/step08_runtime_context/) | Know the logged-in customer; show only their orders | `context_schema`, `ToolRuntime`, `@dynamic_prompt` |

### Part 3 · Knowledge: RAG (steps 09–10, about 30 minutes)

| # | Step | Barista Bot can now… | LangChain concepts |
| --- | --- | --- | --- |
| 09 | [Search the handbook](steps/step09_retrieval/) | Find the policy paragraph that answers a question | `Document`, text splitters, `init_embeddings`, `InMemoryVectorStore` |
| 10 | [RAG agent](steps/step10_rag_agent/) | Answer policy questions with sources, or say it doesn't know | Retrieval as a tool, agentic RAG, citations |

### Part 4 · Ready for real customers (steps 11–13, about 50 minutes)

| # | Step | Barista Bot can now… | LangChain concepts |
| --- | --- | --- | --- |
| 11 | [Middleware](steps/step11_middleware/) | Mask card numbers, cap runaway loops, summarise long chats | `PIIMiddleware`, `ModelCallLimitMiddleware`, `SummarizationMiddleware`, `@before_model`, `@wrap_tool_call` |
| 12 | [Human in the loop](steps/step12_human_in_the_loop/) | Ask a human before issuing a refund | `HumanInTheLoopMiddleware`, interrupts, `Command(resume=...)` |
| 13 | [A team of agents](steps/step13_multi_agent/) | Hand work to an orders specialist and a policy specialist | Sub-agents as tools, `response_format`, `subgraphs=True` |

**Step 13 is the finished Barista Bot.** If you stop here, you have used every core part of LangChain.

### After the course (step 14)

Not a Barista Bot step, and self-paced: a tour of 16 more features, each with what it is, when to use it,
an example and a docs link, plus five small files you can run:

| Example | Shows |
| --- | --- |
| [`fallback_and_retry.py`](steps/step14_next_level/fallback_and_retry.py) | Switch to a backup model when one fails |
| [`stream_tokens.py`](steps/step14_next_level/stream_tokens.py) | Stream an agent's answer token by token |
| [`long_term_memory.py`](steps/step14_next_level/long_term_memory.py) | Remember a customer across conversations |
| [`custom_graph.py`](steps/step14_next_level/custom_graph.py) | Build your own workflow with LangGraph |
| [`fake_model_test.py`](steps/step14_next_level/fake_model_test.py) | Test tools, chains and agents without calling a model |

Start with the [step 14 README](steps/step14_next_level/).

## How to read a step

```text
langchain-step-by-step/
├── shared/                  # boilerplate: you can skip this folder
│   ├── config.py            #   loads .env, picks MODEL and EMBEDDING_MODEL
│   ├── console.py           #   run_demo(), print_updates(): running and printing
│   ├── shop.py              #   fake products, customers and orders
│   └── handbook/*.md        #   the shop's policy handbook (searched from step 09)
└── steps/
    └── stepNN_name/
        ├── app.py           # THE LESSON: everything new in this step is here
        ├── shop_tools.py    # from step 07: code from earlier steps, moved out of app.py
        ├── knowledge.py     #   (unchanged; only there to keep app.py short)
        └── README.md        # the lesson text
```

**Only `app.py` is the lesson.** `shared/` holds what isn't LangChain: loading `.env`, printing output
nicely, fake shop data. From step 07 on, code you learned in an earlier step moves to a helper file next to
`app.py` (`shop_tools.py`, `knowledge.py`, `guardrails.py`, `review.py`), unchanged, so `app.py` stays
about the new feature. Each helper file's docstring says which step it came from.

Every step README has the same sections:

| Section | What it holds |
| --- | --- |
| **What changed** | A table of what was added, changed and removed since the previous step |
| **Why** | The limit Barista Bot hit, and how the new feature fixes it |
| **Key concepts** | The new ideas, in plain words |
| **Key code** | The few lines that matter, explained in a table |
| **Run it** | The exact commands |
| **Try these prompts** | Prompts that show the new feature, and one that shows its limit (which the next step fixes) |
| **Look at the output** | What to notice in what gets printed |
| **Break it** | One small change that fails, so you see the error and understand the feature |
| **Recap** and **Learn more** | What to remember, and links to the official docs |

In the code, comments mark what is new:

```python
agent = create_agent(
    model=model,
    tools=[list_my_orders, get_order_status, search_products, check_stock],  # CHANGED
    middleware=[personalised_prompt],  # NEW: sets the system prompt on every call
    # REMOVED: system_prompt=SYSTEM_PROMPT. personalised_prompt replaces it.
    context_schema=CustomerContext,  # NEW: the type of context this agent expects
)
```

**Reading the output.** Steps print what happens as it happens:

```text
[user (C-001)] Where is my order BS-1002?        your message (and the logged-in customer)
[barista_bot] -> calls get_order_status(...)     the model asked for a tool
[barista_bot] <- get_order_status returned ...   the tool's result, sent back to the model
[barista_bot] Your order has shipped ...          the answer
```

**See a lesson as a diff.** Steps are full copies, so you can compare any two:

```bash
git diff --no-index steps/step05_first_tool/app.py steps/step06_first_agent/app.py
```

**Jump anywhere.** Every step runs on its own. Skip ahead, go back, or start over from any step.

All orders, stock and policies are fake data in `shared/`, so results are predictable and nothing is ever
charged or refunded. Apart from calls to Gemini (and to LangSmith, if you turn it on), nothing uses the
internet. Model answers vary from run to run: yours will be worded differently from the examples in the
READMEs, but should show the same behaviour.

## Troubleshooting

| Problem | Fix |
| --- | --- |
| `GOOGLE_API_KEY is not set` | Copy `.env.example` to `.env` in the repo **root** and paste your key, with no quotes or spaces. |
| `ModuleNotFoundError: No module named 'shared'` | Activate the virtual environment, then run `pip install -r requirements.txt` again from the repo root. |
| `ModuleNotFoundError: No module named 'langchain'` | The virtual environment isn't active (setup step 2). |
| `API key not valid` / 400 / 403 | Check the key in `.env`. Create a new one at Google AI Studio if needed. |
| `429` / `RESOURCE_EXHAUSTED` | Free-tier rate limit. Wait a minute and try again, or set `MODEL=google_genai:gemini-flash-lite-latest` in `.env`. |
| `404` / model not found | Google renamed or retired the model. Check [the model list](https://ai.google.dev/gemini-api/docs/models) and update `MODEL` in `.env`. |
| `.ps1 cannot be loaded because running scripts is disabled` (Windows) | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use `.venv\Scripts\activate.bat` from `cmd`. |
| `₹` or Hindi text shows as `?` (Windows) | Use Windows Terminal, or run `chcp 65001` first. |
| Step 12/13 waits forever | It's waiting for you: type `a`, `e` or `r` and press Enter at the `[review]` prompt. |
| A step's answer differs from its README | Expected: models aren't deterministic. If it's very different, run it again, then compare what the tools returned (the `<-` lines). |

Still stuck? [Open an issue](https://github.com/ease-my-work/langchain-step-by-step/issues) with the step,
the command you ran and the full error (remove your API key first).

## For contributors

```bash
pip install -r requirements-dev.txt
ruff check . && ruff format --check .
python scripts/check_steps.py     # imports every step and runs step 14's tests; no API key needed
```

CI runs the same checks on Python 3.10 and 3.14. LangChain versions are pinned in `requirements.txt`;
when you bump them, also run every step against a real model before merging.

## License

Code and docs are licensed under the [Apache License 2.0](LICENSE).

This is an independent learning resource. It is not an official LangChain product and is not endorsed by
LangChain, Inc. or Google. Bean Street Coffee and its customers are made up.
