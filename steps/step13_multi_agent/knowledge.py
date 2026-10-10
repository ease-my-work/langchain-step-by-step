"""The handbook index from step 09 and the search_handbook tool from step 10 (unchanged).

They moved here to keep app.py about what is new in this step.
"""

from langchain.embeddings import init_embeddings
from langchain.tools import tool
from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

from shared import EMBEDDING_MODEL, HANDBOOK_DIR

# An embedding model turns text into a list of numbers (a vector). Texts with similar
# meaning get vectors that are close together, even when they share no words.
embeddings = init_embeddings(EMBEDDING_MODEL)

# A vector store keeps chunks with their vectors and finds the closest ones to a query.
# InMemoryVectorStore lives in this process; Chroma, pgvector, Pinecone and others work the same.
vector_store = InMemoryVectorStore(embeddings)


def load_handbook() -> list[Document]:
    """One Document per Markdown file. A Document is text plus metadata."""
    return [
        Document(page_content=path.read_text(encoding="utf-8"), metadata={"source": path.name})
        for path in sorted(HANDBOOK_DIR.glob("*.md"))
    ]


# Splitters cut documents into chunks small enough to match one idea each.
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
    # add_documents() embeds every chunk (one call to the embedding model per batch)
    # and stores it with its vector.
    vector_store.add_documents(chunks)
    print(f"[index] {len(documents)} files -> {len(chunks)} chunks embedded")


@tool
def search_handbook(query: str) -> str:
    """Search Bean Street Coffee's policy handbook: shipping, returns, refunds, warranty,
    the Bean Points loyalty programme, and brewing guides.

    Args:
        query: What to look for, in plain words, like "return opened beans".
    """
    chunks = vector_store.similarity_search(query, k=3)
    # Label every chunk with where it came from, so the model can cite it.
    return "\n\n".join(
        f"[{chunk.metadata['source']} > {chunk.metadata.get('section', 'intro')}]\n"
        f"{chunk.page_content}"
        for chunk in chunks
    )
