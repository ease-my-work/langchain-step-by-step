# Step 14 · Next level: what else LangChain can do

> **You'll learn:** what else LangChain and LangGraph offer, when you'd use each feature, and where to read more. This is a map for after the course, not a lesson to finish in one sitting.
> **Time:** self-paced · **Previous:** [Step 13 · A team of agents](../step13_multi_agent/)

## How this step works

This step doesn't build a new Barista Bot. Each feature gets:

- **What it is**, in a sentence or two;
- **Use it when**: the problem it solves;
- **An example**: a runnable file in this folder (marked **▶ runnable**), or a short snippet;
- **Learn more**: the official docs.

Run a file from the repo root:

```bash
python steps/step14_next_level/fallback_and_retry.py
```

Every runnable file was run against Gemini Flash with LangChain 1.4 while writing this page, except
`fake_model_test.py`, which needs no model at all. **Snippets without a file were not run**; some need an
extra package (named in each section). The docs links are the source of truth.

**Suggested order after the course:** LangSmith tracing (5) → testing (6) → durable checkpointers (7) →
streaming tokens (3) → deployment (16). That's the shortest path from "I understand LangChain" to "I shipped
an agent".

## Contents

| # | Feature | Example |
| --- | --- | --- |
| 1 | [Other model providers](#1-other-model-providers) | snippet |
| 2 | [Model fallback and retries](#2-model-fallback-and-retries) | ▶ `fallback_and_retry.py` |
| 3 | [Streaming tokens from an agent](#3-streaming-tokens-from-an-agent) | ▶ `stream_tokens.py` |
| 4 | [Long-term memory](#4-long-term-memory) | ▶ `long_term_memory.py` |
| 5 | [Tracing with LangSmith](#5-tracing-with-langsmith) | `.env` only |
| 6 | [Testing without a model](#6-testing-without-a-model) | ▶ `fake_model_test.py` |
| 7 | [Durable checkpointers](#7-durable-checkpointers) | snippet |
| 8 | [Your own workflow with LangGraph](#8-your-own-workflow-with-langgraph) | ▶ `custom_graph.py` |
| 9 | [More built-in middleware](#9-more-built-in-middleware) | snippet |
| 10 | [Tool artifacts](#10-tool-artifacts) | snippet |
| 11 | [MCP tools](#11-mcp-tools) | snippet |
| 12 | [Images and other inputs](#12-images-and-other-inputs) | snippet |
| 13 | [Async](#13-async) | snippet |
| 14 | [LangSmith Studio](#14-langsmith-studio) | snippet |
| 15 | [Deep Agents](#15-deep-agents) | link |
| 16 | [Deployment and evaluation](#16-deployment-and-evaluation) | link |

---

## 1. Other model providers

**What it is.** `init_chat_model("provider:model")` works with dozens of providers. Every step reads its
model from `MODEL` in `.env`, so you can run the whole course on another one.

**Use it when** you want to compare models, cut cost, run locally, or avoid depending on one vendor.

**Example.** Install the provider's package, set its key, and change `.env`:

```bash
pip install langchain-anthropic   # or langchain-openai, langchain-ollama, ...
```

```text
MODEL=anthropic:claude-sonnet-5-5      # needs ANTHROPIC_API_KEY
MODEL=openai:gpt-5-mini                # needs OPENAI_API_KEY
MODEL=ollama:llama3.2                  # local, no key (needs Ollama running)
```

Steps 09–13 also need an embedding model: set `EMBEDDING_MODEL` too (for example
`openai:text-embedding-3-small`), or keep Gemini's. Smaller local models may follow the tool and
formatting rules less reliably than the default.

**Learn more:** [Models](https://docs.langchain.com/oss/python/langchain/models) ·
[Chat model integrations](https://docs.langchain.com/oss/python/integrations/chat)

## 2. Model fallback and retries

**▶ runnable:** [`fallback_and_retry.py`](fallback_and_retry.py)

**What it is.** `ModelFallbackMiddleware(backup, ...)` switches to another model when a call fails.
`ModelRetryMiddleware` retries a failed call with growing waits. It retries passing problems (timeouts,
rate limits) but not errors that can't pass, like a wrong model name.

**Use it when** your app must answer even when a provider is down or rate-limited.

**What we saw.** The file's primary model name is deliberately wrong:

```text
[middleware] gemini-model-that-does-not-exist failed: GoogleModelNotFoundError
[middleware] gemini-flash-latest answered
[barista_bot] Store your beans in an airtight, opaque container ...
```

**Learn more:** [Prebuilt middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in)

## 3. Streaming tokens from an agent

**▶ runnable:** [`stream_tokens.py`](stream_tokens.py)

**What it is.** `stream_mode="updates"` (the course) yields each finished step. `stream_mode="messages"`
yields `(chunk, metadata)` pairs as the model writes, from inside the agent loop. `metadata["langgraph_node"]`
says whether a chunk came from the model or a tool. You can pass a list, like
`stream_mode=["updates", "messages"]`, to get both.

**Use it when** you build a chat UI that "types" the answer.

**Learn more:** [Streaming](https://docs.langchain.com/oss/python/langchain/streaming)

## 4. Long-term memory

**▶ runnable:** [`long_term_memory.py`](long_term_memory.py)

**What it is.** A **store** saves JSON documents under a namespace and key, shared by every thread. Tools
read and write it through `runtime.store`. The checkpointer (step 07) remembers *one conversation*; the
store remembers *a customer*.

**Use it when** the agent should remember preferences or facts across conversations.

**What we saw.** On "Monday", Asha says she loves dark, smoky coffee and brews with a South Indian filter;
the agent calls `save_preference`. On "Friday", a **new thread**, it calls `recall_preferences` and
`list_beans`, and recommends the Chikmagalur Dark Roast.

**Learn more:** [Long-term memory](https://docs.langchain.com/oss/python/langchain/long-term-memory)

## 5. Tracing with LangSmith

**What it is.** LangSmith records every run as a tree: each model call with its exact prompt, response,
tokens and latency; each tool call; each middleware step and sub-agent.

**Use it when** always, while developing. "Why did it do that?" is answered in seconds.

**Example.** No code. Create a free account at [smith.langchain.com](https://smith.langchain.com), then
remove the `# ` from the three `LANGSMITH_*` lines in `.env` and add your key. Run any step and open the
project `langchain-step-by-step`.

**Learn more:** [LangSmith observability](https://docs.langchain.com/oss/python/langchain/observability)

## 6. Testing without a model

**▶ runnable:** [`fake_model_test.py`](fake_model_test.py) (no API key needed; CI runs it)

**What it is.** `GenericFakeChatModel` returns replies you script in advance. Tests become fast, free and
repeatable. Tools are plain objects you can test with `.invoke({...})`. For agents, a tiny subclass adds
`bind_tools`, and you script the tool calls too.

**Use it when** you want unit tests for tools, chains and the agent's wiring (did the tool run, did its
result reach the model?). Test the model's *judgement* with evaluations instead (section 16).

**Learn more:** [Test](https://docs.langchain.com/oss/python/langchain/test)

## 7. Durable checkpointers

**What it is.** `InMemorySaver` forgets everything when the process stops. Database-backed checkpointers
keep threads (and paused human-in-the-loop runs) across restarts and servers. Same interface.

**Use it when** anything leaves your laptop.

**Example** (needs `pip install langgraph-checkpoint-postgres`; for SQLite, `langgraph-checkpoint-sqlite`
and `SqliteSaver`):

```python
from langgraph.checkpoint.postgres import PostgresSaver

with PostgresSaver.from_conn_string("postgresql://user:pass@localhost:5432/shop") as checkpointer:
    checkpointer.setup()  # creates the tables, once
    agent = create_agent(model, tools, checkpointer=checkpointer)
```

**Learn more:** [Short-term memory: in production](https://docs.langchain.com/oss/python/langchain/short-term-memory)

## 8. Your own workflow with LangGraph

**▶ runnable:** [`custom_graph.py`](custom_graph.py)

**What it is.** `create_agent` is built on **LangGraph**: a graph of nodes (Python functions) sharing a
state, joined by edges. When you know the steps, you can draw the graph yourself: fixed order, branches,
loops, parallel steps, and the same checkpointer, interrupts and streaming as agents. A node can call an
agent, and an agent's tool can run a graph.

**Use it when** the process is fixed and must be reliable (approval flows, pipelines with retries), or
when you need control `create_agent` doesn't give you. Step 04's chain becomes a graph in this file:

```text
START -> triage -> (urgent?) -> escalate -> END
                             -> reply    -> END
```

The file prints the graph as Mermaid; paste it into [mermaid.live](https://mermaid.live) to see it.

**Learn more:** [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) ·
[Graph API](https://docs.langchain.com/oss/python/langgraph/graph-api)

## 9. More built-in middleware

**What it is.** Step 11 used four. A few more:

| Middleware | Does |
| --- | --- |
| `ToolCallLimitMiddleware(tool_name="search_handbook", run_limit=3)` | Caps calls to one tool (or all tools) per run or thread |
| `LLMToolSelectorMiddleware(max_tools=3)` | A cheap model picks the relevant tools first, for agents with many tools |
| `ContextEditingMiddleware(edits=[ClearToolUsesEdit(trigger=50_000)])` | Clears old tool results when the context gets big |
| `TodoListMiddleware()` | Gives the agent a `write_todos` tool to plan long tasks |
| `PIIMiddleware("upi_id", detector=r"[\w.]+@[a-z]+", strategy="redact")` | Your own PII type, from a regex |

**Learn more:** [Prebuilt middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in)

## 10. Tool artifacts

**What it is.** A tool can return two things: `content` for the model, and an `artifact` for your app
(full documents, a chart, raw rows) that is kept on the `ToolMessage` but **not sent** to the model.

**Use it when** the model needs a summary but your UI needs the full data, such as linkable sources for
step 10's answers.

```python
@tool(response_format="content_and_artifact")
def search_handbook(query: str):
    """Search the policy handbook."""
    chunks = vector_store.similarity_search(query, k=3)
    text = "\n\n".join(chunk.page_content for chunk in chunks)
    return text, chunks  # (content, artifact): message.artifact holds the Documents
```

**Learn more:** [Tools](https://docs.langchain.com/oss/python/langchain/tools)

## 11. MCP tools

**What it is.** The Model Context Protocol lets an agent use tools served by other programs (file systems,
GitHub, databases, your company's services) without writing a wrapper for each one.

**Use it when** the tool you need already exists as an MCP server.

**Example** (needs `pip install langchain-mcp-adapters`; the server here is a placeholder):

```python
from langchain_mcp_adapters.client import MultiServerMCPClient

client = MultiServerMCPClient(
    {"shop_db": {"transport": "streamable_http", "url": "http://localhost:8000/mcp"}}
)
tools = await client.get_tools()  # MCP tools, as LangChain tools
agent = create_agent(model, tools)
```

**Learn more:** [Model Context Protocol](https://docs.langchain.com/oss/python/langchain/mcp)

## 12. Images and other inputs

**What it is.** Messages can hold content blocks: text, images, audio, files. Models that accept them
(Gemini does) read them all.

**Use it when** a customer sends a photo of a torn bag, as step 12's policy asks for.

```python
message = {
    "role": "user",
    "content": [
        {"type": "text", "text": "My bag arrived like this. Can I get a refund?"},
        {"type": "image", "url": "https://example.com/torn-bag.jpg"},
    ],
}
agent.invoke({"messages": [message]}, config, context=context)
```

**Learn more:** [Messages: multimodal](https://docs.langchain.com/oss/python/langchain/messages)

## 13. Async

**What it is.** Every runnable has async twins: `ainvoke`, `astream`, `abatch`. Tools can be `async def`.

**Use it when** you serve many users from one process (FastAPI and other async web frameworks).

```python
result = await agent.ainvoke({"messages": [...]}, config, context=context)
async for chunk in agent.astream({"messages": [...]}, config, stream_mode="updates"):
    ...
```

**Learn more:** [Agents](https://docs.langchain.com/oss/python/langchain/agents)

## 14. LangSmith Studio

**What it is.** A visual debugger for agents and graphs: chat with the agent, see each step, edit state,
replay from any point. It connects to a local dev server started with `langgraph dev`.

**Use it when** you want the "click through what happened" experience of a dev UI.

**Example** (needs `pip install "langgraph-cli[inmem]"` and a free LangSmith account; this repo isn't
wired up for it, so treat this as a starting point). Add `langgraph.json` at the repo root:

```json
{
  "dependencies": ["."],
  "graphs": {"barista_bot": "./steps/step06_first_agent/app.py:agent"},
  "env": ".env"
}
```

Then run `langgraph dev` and open the Studio link it prints.

**Learn more:** [LangSmith Studio](https://docs.langchain.com/oss/python/langchain/studio) ·
[Run a local server](https://docs.langchain.com/oss/python/langgraph/local-server)

## 15. Deep Agents

**What it is.** `deepagents` is a ready-made agent built on `create_agent` for long, multi-step work:
planning with a to-do list, a virtual file system for notes, and sub-agents it spawns itself.

**Use it when** tasks take many steps and lots of context: research, coding, report writing. For a support
bot like Barista Bot, `create_agent` is the better fit.

**Learn more:** [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview)

## 16. Deployment and evaluation

**What it is.** An agent is a runnable, so you can serve it from any Python web app (FastAPI, Django), or
deploy it to LangSmith's managed agent server, which adds durable threads, background runs and an API.
Before you ship, **evaluate**: run the agent on a dataset of real questions and score the answers
(correct order facts? cited the right policy? refused off-topic requests?) every time you change a prompt
or model.

**Use it when** real customers are next.

**Learn more:** [Deployment](https://docs.langchain.com/oss/python/langchain/deploy) ·
[LangSmith observability and evaluation](https://docs.langchain.com/oss/python/langchain/observability)
