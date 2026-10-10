"""Step 09 - Search the handbook.

The first half of RAG (retrieval-augmented generation): load the shop's policy handbook, split it
into small chunks, turn each chunk into an embedding, and find the chunks that best match a
question. No agent in this step, so you can see retrieval on its own.
"""

from langchain.embeddings import init_embeddings
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from shared import EMBEDDING_MODEL, HANDBOOK_DIR, run_demo

# NEW: an embedding model turns text into a list of numbers (a vector). Texts with similar
# meaning get vectors that are close together, even when they share no words.
embeddings = init_embeddings(EMBEDDING_MODEL)

# NEW: a vector store keeps chunks with their vectors and finds the closest ones to a query.
# InMemoryVectorStore lives in this process; Chroma, pgvector, Pinecone and others work the same.
vector_store = InMemoryVectorStore(embeddings)


def load_handbook() -> list[Document]:
    """NEW: one Document per Markdown file. A Document is text plus metadata."""
    return [
        Document(page_content=path.read_text(encoding="utf-8"), metadata={"source": path.name})
        for path in sorted(HANDBOOK_DIR.glob("*.md"))
    ]


# NEW: splitters cut documents into chunks small enough to match one idea each.
# 1. Split at Markdown headings, keeping each heading in the chunk's metadata.
header_splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[("#", "page"), ("##", "section")],
    strip_headers=False,
)
# 2. Cut any section that is still long into pieces of at most ~600 characters.
size_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)


def split(documents: list[Document]) -> list[Document]:
    chunks = []
    for document in documents:
        for section in header_splitter.split_text(document.page_content):
            section.metadata["source"] = document.metadata["source"]
            chunks.append(section)
    return size_splitter.split_documents(chunks)


def build_index() -> None:
    """Loads, splits and embeds the handbook. Runs once, at startup."""
    documents = load_handbook()
    chunks = split(documents)
    # NEW: add_documents() embeds every chunk (one call to the embedding model per batch)
    # and stores it with its vector.
    vector_store.add_documents(chunks)
    print(f"[index] {len(documents)} files -> {len(chunks)} chunks embedded")


def ask(question: str) -> None:
    # NEW: embed the question and return the k closest chunks, each with a similarity score
    # (higher is closer, at most 1.0).
    results = vector_store.similarity_search_with_score(question, k=3)
    for chunk, score in results:
        where = f"{chunk.metadata['source']} > {chunk.metadata.get('section', 'intro')}"
        preview = " ".join(chunk.page_content.split())[:110]
        print(f"[search] {score:.2f}  {where}\n         {preview}...")


DEMO_PROMPTS = [
    "Can I return a bag of beans I already opened?",
    "How long until my refund shows up in my bank?",
    "Do gold members pay for express delivery?",
    "My espresso is coming out sour",
    "Do you ship to Singapore?",
    "What's the capital of France?",
]

if __name__ == "__main__":
    build_index()  # NEW: index once, before the first question
    run_demo(ask, DEMO_PROMPTS)
