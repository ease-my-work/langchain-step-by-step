# Step 09 · Search the handbook

> **You'll learn:** the retrieval half of RAG: documents, splitting, embeddings and a vector store, so you can find the passages that answer a question.
> **Time:** about 15 minutes · **Previous:** [Step 08 · Runtime context](../step08_runtime_context/) · **Next:** [Step 10 · RAG agent](../step10_rag_agent/)

## What changed

A detour with **no agent and no chat model**, so you can see retrieval on its own. Step 10 plugs it into
Barista Bot.

| Added | Changed | Removed |
| --- | --- | --- |
| `embeddings = init_embeddings(EMBEDDING_MODEL)` | `ask()` searches the handbook and prints the 3 best chunks with scores | The chat model and the agent (back in step 10) |
| `vector_store = InMemoryVectorStore(embeddings)` | | |
| `load_handbook()`: one `Document` per Markdown file in [`shared/handbook/`](../../shared/handbook/) | | |
| `split()`: `MarkdownHeaderTextSplitter`, then `RecursiveCharacterTextSplitter` | | |
| `build_index()`: load, split, embed and store, once at startup | | |

There's no useful diff with step 08: this file is all new.

## Why

Customers ask about policies: returns, refunds, shipping, warranty, loyalty points. The answers are in
the shop's handbook (five Markdown files), not in the model's training. You can't paste the whole handbook
into every prompt: real handbooks are far too long, and long prompts are slow and expensive. Instead, find
the **few paragraphs** that matter for this question and send only those. That's **retrieval**; feeding the
result to a model is **retrieval-augmented generation (RAG)**.

## Key concepts

- **`Document`.** Text (`page_content`) plus `metadata` (here: which file, which section). Loaders in
  LangChain's integration packages create Documents from PDFs, web pages, Notion, databases and more; here,
  three lines of Python read Markdown files.
- **Splitting (chunking).** A whole file matches many questions a little. Small chunks, about one idea
  each, match one question well. We split twice:
  1. `MarkdownHeaderTextSplitter` cuts at `#` and `##` headings and records them in metadata
     (`page`, `section`), so every chunk knows where it came from.
  2. `RecursiveCharacterTextSplitter` cuts any section still over ~600 characters, preferring paragraph,
     then line, then word breaks. `chunk_overlap` repeats a little text across cuts so no sentence is lost.
- **Embedding.** A list of numbers (3,072 of them for `gemini-embedding-001`) that captures what a text
  *means*. "How long until my refund shows up in my bank?" and "The money usually reaches the customer's
  account 5 to 7 working days..." share almost no words, but their embeddings are close.
- **Vector store.** Stores each chunk with its embedding. `similarity_search(query, k)` embeds the query
  and returns the `k` closest chunks. `InMemoryVectorStore` lives in your process; Chroma, pgvector, Qdrant,
  Pinecone and others have the same methods.
- **Similarity score.** Cosine similarity, at most 1.0. Higher is closer. Useful for spotting weak matches.

## Key code

```python
embeddings = init_embeddings(EMBEDDING_MODEL)  # "google_genai:gemini-embedding-001"
vector_store = InMemoryVectorStore(embeddings)

documents = [
    Document(page_content=path.read_text(), metadata={"source": path.name}) for path in ...
]

header_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "page"), ("##", "section")], strip_headers=False
)
size_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)

vector_store.add_documents(chunks)  # embed and store
results = vector_store.similarity_search_with_score(question, k=3)  # [(Document, score), ...]
```

| Part | What it does |
| --- | --- |
| `init_embeddings("provider:model")` | Like `init_chat_model`, for embedding models. |
| `metadata={"source": path.name}` | Travels with every chunk. Step 10 uses it to cite sources. |
| `strip_headers=False` | Keeps the heading text in the chunk too, which helps matching. |
| `add_documents(chunks)` | Calls the embedding model for all chunks (in batches) and stores the vectors. Do this once, not per question. |
| `similarity_search_with_score(q, k=3)` | Embeds the question (one call) and returns the 3 closest chunks with scores. |

## Run it

```bash
python steps/step09_retrieval/app.py
python steps/step09_retrieval/app.py "Is the espresso machine warranty longer than the grinder's?"
```

The first line shows the index being built: `5 files -> 26 chunks embedded`.

## Try these prompts

1. `Can I return a bag of beans I already opened?` Top hit: `returns_and_refunds.md > Coffee beans`
   ("opened bags of beans cannot be returned"), score ~0.79.
2. `How long until my refund shows up in my bank?` Top hit: `Refunds` ("5 to 7 working days"), though the
   question shares few words with it. That's meaning-based search.
3. `Do gold members pay for express delivery?` Two good hits from two files: `shipping.md > Shipping
   charges` and `loyalty_programme.md > Tiers`. Answers often need more than one chunk; that's why `k=3`.
4. `My espresso is coming out sour` `brewing_guide.md > Espresso` ("Fast and sour? Grind finer").
5. `Do you ship to Singapore?` `shipping.md`'s intro: "We do not ship outside India yet."
6. `What's the capital of France?` **The limit:** you still get three results, the best of a bad lot
   (`French press`, score ~0.57). A vector store always returns its `k` nearest chunks, relevant or not.
   Something has to judge whether they answer the question: in step 10, the model does.

## Look at the output

```text
[user] Do gold members pay for express delivery?
[search] 0.75  shipping.md > Shipping charges
         ## Shipping charges - Standard shipping is free on orders of ₹999 or more. ...
[search] 0.71  loyalty_programme.md > Tiers
         ## Tiers Tiers are based on what a customer spent in the last 12 months: ...
[search] 0.64  loyalty_programme.md > Expiry
         ...
```

Compare the scores of good answers (0.7–0.8) with the off-topic question (~0.56). Scores depend on the
embedding model, so measure them for yours before using a cut-off.

## Break it

Make the chunks tiny: `RecursiveCharacterTextSplitter(chunk_size=80, chunk_overlap=0)`, and ask prompt 2.
The index grows to many more chunks, and the top three for the refund question are now fragments like
`issue the refund....` and `refund....`: they match the words but have lost the facts. Chunks too big
dilute the match; chunks too small lose their meaning. Splitting at headings first, as this step does, keeps
each chunk a complete thought.

## Recap

- Retrieval = load `Document`s, split them into chunks, embed the chunks, store them in a vector store,
  search with `similarity_search`.
- Embeddings match by meaning, not by shared words.
- Keep metadata (source, section) on every chunk: you'll cite it.
- A vector store always returns its top `k`; something still has to judge relevance.

## Learn more

- [Retrieval](https://docs.langchain.com/oss/python/langchain/retrieval)
- [Build a semantic search engine](https://docs.langchain.com/oss/python/langchain/knowledge-base) (the official tutorial for this step)
- Integrations: [document loaders](https://docs.langchain.com/oss/python/integrations/document_loaders),
  [text splitters](https://docs.langchain.com/oss/python/integrations/splitters),
  [embeddings](https://docs.langchain.com/oss/python/integrations/text_embedding),
  [vector stores](https://docs.langchain.com/oss/python/integrations/vectorstores)
