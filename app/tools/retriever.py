"""
Enhanced RAG (Retrieval-Augmented Generation) pipeline using FAISS.

FAISS is used instead of ChromaDB because:
- Thread-safe for concurrent reads (supports parallel agents)
- No sqlite dependency (avoids Windows segfault issues)
- Pure in-memory vector search with disk persistence via pickle
"""
import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.messages import HumanMessage

from app.core.logger import get_logger

logger = get_logger("rag")

PERSIST_DIRECTORY = "./nba_knowledge_db"

_vector_store_cache = None


def get_vector_store():
    """Load FAISS vector store from disk (cached in memory after first load)."""
    global _vector_store_cache
    if _vector_store_cache is not None:
        return _vector_store_cache

    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY not found in environment variables")

    embeddings = DashScopeEmbeddings(
        model="text-embedding-v1",
        dashscope_api_key=api_key,
    )

    index_path = os.path.join(PERSIST_DIRECTORY, "index.faiss")
    if not os.path.exists(index_path):
        logger.warning(f"FAISS index not found at {index_path}, RAG unavailable")
        return None

    _vector_store_cache = FAISS.load_local(
        PERSIST_DIRECTORY, embeddings, allow_dangerous_deserialization=True
    )
    logger.info(f"FAISS vector store loaded from {PERSIST_DIRECTORY}")
    return _vector_store_cache


def query_knowledge_base(query: str, k: int = 3) -> str:
    """
    RAG retrieval pipeline: query FAISS for similar historical games.

    Returns formatted context string for the LLM prompt.
    """
    try:
        db = get_vector_store()
        if db is None:
            return "No historical knowledge base available. Run ingest_data.py to build it."

        results = db.similarity_search(query, k=k)

        if not results:
            return "No relevant historical data found."

        context_str = ""
        for idx, doc in enumerate(results):
            source = doc.metadata.get("source", "Unknown")
            context_str += f"\n--- Reference {idx + 1} (Source: {source}) ---\n{doc.page_content}\n"

        logger.info(f"RAG retrieved {len(results)} documents for query")
        return context_str

    except Exception as e:
        logger.error(f"RAG retrieval error: {e}")
        return "No relevant historical data found (Retrieval system failure)."
