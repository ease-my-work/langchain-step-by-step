# Step 10 · RAG agent

> **You'll learn:** how to give an agent a knowledge base as a tool, so it answers from your documents, cites them, and says "I don't know" when they don't cover the question.
> **Time:** about 15 minutes · **Previous:** [Step 09 · Search the handbook](../step09_retrieval/) · **Next:** [Step 11 · Middleware](../step11_middleware/)

## What changed

Step 08's Barista Bot plus step 09's handbook search.

| Added | Changed | Removed |
| --- | --- | --- |
| `search_handbook(query)`: a tool that searches the vector store and labels each chunk with its source | `SYSTEM_PROMPT`: answer policy questions only from the handbook, cite the source, admit when it isn't there | |
| `build_index()` before the first question | Step 09's index code moved to [`knowledge.py`](knowledge.py); step 08's tools and `CustomerContext` to [`shop_tools.py`](shop_tools.py) | |

```bash
git diff --no-index steps/step08_runtime_context/app.py steps/step10_rag_agent/app.py
```

## Why

Step 08 could check orders but not policies. Step 09 could find policy paragraphs but not talk. Joined,
Barista Bot can answer "Can I return opened beans?" with the shop's real rule, and show where it came from.

There are two common ways to join them:

| | **2-step RAG** (a chain) | **Agentic RAG** (this step) |
| --- | --- | --- |
| How | Always search with the user's message, then call the model with the results | Retrieval is a tool; the agent decides when and what to search |
| Good for | Q&A over documents, nothing else | Assistants that also chat, use other tools, or need several searches |
| Cost | One search and one model call | The model may search zero, one or several times |

Barista Bot already is an agent, so retrieval becomes one more tool.

## Key concepts

- **Retriever as a tool.** `search_handbook` is a normal `@tool`. The agent writes the search query, which
  is often better than the raw message ("Do I have to pay for express shipping?" → `"express shipping"`).
- **Grounding.** The prompt says: policy answers come only from `search_handbook` results. Retrieval gives
  the facts; the rule stops the model filling gaps from its training.
- **Citations.** Each chunk in the tool's output starts with `[file > section]`, from the metadata saved in
  step 09. The model copies that into its answer.
- **Saying "I don't know".** The vector store always returns 3 chunks, even for an unanswerable question
  (step 09's limit). The model reads them, sees they don't answer, and can search again or give up honestly.
- **Index once.** `build_index()` runs at startup, not per question. In production, the index lives in a
  database and is built by a separate job when documents change.

## Key code

```python
@tool
def search_handbook(query: str) -> str:
    """Search Bean Street Coffee's policy handbook: shipping, returns, refunds, warranty,
    the Bean Points loyalty programme, and brewing guides. ..."""
    chunks = vector_store.similarity_search(query, k=3)
    return "\n\n".join(
        f"[{chunk.metadata['source']} > {chunk.metadata.get('section', 'intro')}]\n"
        f"{chunk.page_content}"
        for chunk in chunks
    )
```

And in the prompt:

```text
- Answer policy and brewing questions only from search_handbook results, never from general
  knowledge. End such answers with the source in brackets, like (returns_and_refunds.md > Refunds).
- If the handbook does not answer the question, say you don't know and offer to pass it to a human.
```

| Part | What it does |
| --- | --- |
| The docstring | Lists the topics, so the model knows which questions to search for. |
| `similarity_search(query, k=3)` | Step 09's search. The model wrote `query`. |
| `[source > section]` labels | What the model cites. Without them it would have to guess where text came from. |
| Returning a `str` | One readable block for the model. |

## Run it

```bash
python steps/step10_rag_agent/app.py
python steps/step10_rag_agent/app.py "My grinder's burrs feel dull after a year. Is that covered?"
```

The demo runs as Asha (`C-001`, gold) and Meera (`C-003`, bronze).

## Try these prompts

1. As Asha: `I opened one bag of beans from my last order and don't like the taste. Can I return it?`
   Searches `"return opened beans"`, says opened beans can't be returned (but damaged or stale ones can),
   and cites `(returns_and_refunds.md > Coffee beans)`.
2. As Asha: `Do I have to pay for express shipping?` "As a Gold loyalty member, you receive free express
   shipping." The handbook gives the rule; step 08's context says she's gold.
3. As Meera: the **same question**. "Express shipping costs ₹149 ... as a Bronze member, the standard fee
   applies." Same document, different customer, different answer.
4. As Meera: `How do I make South Indian filter coffee?` Brewing steps from `brewing_guide.md`.
5. As Meera: `Can I pay with Bitcoin?` The handbook doesn't say. When we ran it, the agent searched three
   times (`"payment methods Bitcoin"`, `"payment"`, `"crypto"`), found nothing relevant, and said it
   doesn't know, offering a human. Several searches for one question is agentic RAG at work.

**The limit:** ask `My card was charged twice, here's the number: 4111 1111 1111 1111`. The card number
goes straight into the conversation, the model and the checkpointer. And nothing in code stops a long chat
from growing without limit, or a confused model from looping. Rules in the prompt aren't enough for these.
Step 11 adds guardrails in code.

## Look at the output

```text
[user (C-003)] Do I have to pay for express shipping?
[barista_bot] -> calls search_handbook({'query': 'express shipping'})
[barista_bot] <- search_handbook returned [shipping.md > Shipping charges]
## Shipping charges
- Standard shipping is free on orders of ₹999 or more. Below ₹999 it costs ₹79.
- Express shipping (1 to 2 working days, metro cities only) costs ₹149 on any order.
- Gold loyalty members get free express shipping on every order. ...
[barista_bot] Hello Meera! Yes, express shipping costs ₹149 ... (shipping.md > Shipping charges)
```

The `<-` line shows exactly what the model read. When an answer is wrong, check this first: was the right
chunk retrieved? Most RAG bugs are retrieval bugs.

## Break it

In `main`, replace `build_index()` with `pass`, and ask prompt 1. The store is empty, so
`search_handbook` returns an empty string. The agent says it "found no results" and offers a human,
instead of reciting a generic return policy from its training. Two lessons: index before you search, and
the grounding rule works. An agent that admits it doesn't know is better than one that sounds right.

## Recap

- Agentic RAG: make retrieval a tool; the agent decides when and what to search, and may search again.
- Label chunks with their source so the model can cite them.
- Tell the model to answer only from retrieved text, and to say so when the answer isn't there.
- When a RAG answer is wrong, look at what was retrieved first.

## Learn more

- [Retrieval: agentic RAG and 2-step RAG](https://docs.langchain.com/oss/python/langchain/retrieval)
- [Tools](https://docs.langchain.com/oss/python/langchain/tools)
