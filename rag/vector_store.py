"""
Vector Store - ChromaDB embedding and retrieval for RAG.

Purpose: Embed document chunks into ChromaDB and retrieve relevant passages for
         quiz question generation.
Inputs: List of Document objects (from pdf_loader) for indexing.
        Query string for retrieval.
Outputs: List of relevant Document objects matching the query.
Dependencies: config.py, rag/pdf_loader.py, chromadb, langchain-community.
"""

import os
import config
from rag.pdf_loader import load_pdf

# Number of relevant documents to retrieve per query
TOP_K = 4

# ChromaDB collection name
COLLECTION_NAME = "discover_canada"

_vectorstore = None


def build_vector_store(documents: list = None) -> object:
    """
    Build (or rebuild) the ChromaDB vector store from document chunks.

    Args:
        documents: List of Document objects. If None, loads from PDF automatically.

    Returns:
        A Chroma vector store instance.
    """
    global _vectorstore

    if documents is None:
        documents = load_pdf()

    if not documents:
        raise ValueError("No documents provided to build vector store.")

    print(f"Building vector store with {len(documents)} chunks...")

    try:
        from langchain_community.vectorstores import Chroma
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

        # Use ChromaDB's default embedding function (all-MiniLM-L6-v2)
        # wrapped for LangChain compatibility
        embedding_function = _get_embedding_function()

        persist_dir = config.VECTOR_STORE_PATH
        os.makedirs(persist_dir, exist_ok=True)

        _vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embedding_function,
            collection_name=COLLECTION_NAME,
            persist_directory=persist_dir,
        )
        print(f"Vector store built and persisted at: {persist_dir}")
        return _vectorstore

    except Exception as e:
        raise RuntimeError(f"Failed to build vector store: {e}")


def load_vector_store() -> object:
    """
    Load an existing vector store from disk, or build a new one if it doesn't exist.

    Returns:
        A Chroma vector store instance.
    """
    global _vectorstore

    if _vectorstore is not None:
        return _vectorstore

    persist_dir = config.VECTOR_STORE_PATH
    if os.path.exists(persist_dir) and os.listdir(persist_dir):
        try:
            from langchain_community.vectorstores import Chroma

            embedding_function = _get_embedding_function()
            _vectorstore = Chroma(
                collection_name=COLLECTION_NAME,
                persist_directory=persist_dir,
                embedding_function=embedding_function,
            )
            count = _vectorstore._collection.count()
            if count > 0:
                print(f"Loaded existing vector store with {count} documents.")
                return _vectorstore
        except Exception:
            print("Existing vector store corrupted. Rebuilding...")

    print("No existing vector store found. Building from PDF...")
    return build_vector_store()


def retrieve(query: str, k: int = TOP_K) -> list:
    """
    Retrieve the most relevant document chunks for a given query.

    Args:
        query: The search query string.
        k: Number of documents to retrieve (default: TOP_K).

    Returns:
        A list of Document objects most relevant to the query.
    """
    store = load_vector_store()

    try:
        results = store.similarity_search(query, k=k)
        return results
    except Exception as e:
        print(f"Error during retrieval: {e}")
        return []


class _ChromaDefaultEmbeddings:
    """
    Wrapper around ChromaDB's built-in DefaultEmbeddingFunction
    (onnxruntime all-MiniLM-L6-v2) to make it compatible with LangChain's
    Embeddings interface. No extra packages required beyond chromadb.
    """

    def __init__(self):
        from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
        self._ef = DefaultEmbeddingFunction()

    def embed_documents(self, texts: list) -> list:
        return self._ef(texts)

    def embed_query(self, text: str) -> list:
        return self._ef([text])[0]


def _get_embedding_function():
    """Get the embedding function using ChromaDB's built-in default embeddings."""
    return _ChromaDefaultEmbeddings()


def reset_vector_store():
    """Delete and rebuild the vector store from scratch."""
    global _vectorstore
    import shutil

    persist_dir = config.VECTOR_STORE_PATH
    if os.path.exists(persist_dir):
        shutil.rmtree(persist_dir)
        print("Deleted existing vector store.")

    _vectorstore = None
    return build_vector_store()


if __name__ == "__main__":
    # Build and test retrieval
    store = build_vector_store()
    print("\n--- Testing retrieval ---")
    results = retrieve("What is the capital of Canada?")
    for i, doc in enumerate(results):
        print(f"\nResult {i+1}: {doc.page_content[:120]}...")
