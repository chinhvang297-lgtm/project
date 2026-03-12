"""
Enhanced RAG (Retrieval-Augmented Generation) pipeline.

Features:
- Query Rewriting: LLM rewrites user query into optimized search queries
- Multi-query Retrieval: Searches with multiple query variants for better recall
- LLM Reranking: Uses LLM to rerank retrieved documents by relevance
- Deduplication: Removes duplicate documents across multiple queries
"""
import os
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.messages import HumanMessage

from app.core.logger import get_logger
from app.prompts.templates import QUERY_REWRITE_PROMPT, RERANK_PROMPT

logger = get_logger("rag")

PERSIST_DIRECTORY = "./nba_knowledge_db"


def get_vector_store():
    """Initialize and return the ChromaDB vector store."""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY not found in environment variables")

    embeddings = DashScopeEmbeddings(
        model="text-embedding-v1",
        dashscope_api_key=api_key,
    )

    vector_db = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embeddings,
        collection_name="nba_history",
    )
    return vector_db


def rewrite_query(original_query: str, llm) -> list[str]:
    """
    Use LLM to rewrite a user query into multiple optimized search queries.

    This improves recall by searching from different angles.
    """
    try:
        prompt = QUERY_REWRITE_PROMPT.format(query=original_query)
        response = llm.invoke([HumanMessage(content=prompt)])
        queries = [q.strip() for q in response.content.strip().split("\n") if q.strip()]
        # Always include the original query
        queries = [original_query] + queries[:2]
        logger.info(f"Query rewriting: 1 query -> {len(queries)} queries")
        return queries
    except Exception as e:
        logger.warning(f"Query rewriting failed, using original: {e}")
        return [original_query]


def deduplicate_docs(docs: list) -> list:
    """Remove duplicate documents based on page_content."""
    seen = set()
    unique_docs = []
    for doc in docs:
        content_hash = hash(doc.page_content)
        if content_hash not in seen:
            seen.add(content_hash)
            unique_docs.append(doc)
    return unique_docs


def rerank_documents(query: str, docs: list, llm, top_n: int = 3) -> list:
    """
    Use LLM to rerank retrieved documents by relevance.

    Two-stage retrieval: first retrieve broadly, then rerank precisely.
    """
    if len(docs) <= top_n:
        return docs

    try:
        doc_text = ""
        for idx, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            doc_text += f"\n[Document {idx}] (Source: {source}):\n{doc.page_content}\n"

        prompt = RERANK_PROMPT.format(query=query, documents=doc_text)
        response = llm.invoke([HumanMessage(content=prompt)])

        # Parse ranking: expect comma-separated indices like "3,1,4,2,5"
        ranking_text = response.content.strip()
        indices = []
        for part in ranking_text.split(","):
            part = part.strip()
            if part.isdigit():
                idx = int(part) - 1  # Convert to 0-indexed
                if 0 <= idx < len(docs):
                    indices.append(idx)

        if indices:
            reranked = [docs[i] for i in indices[:top_n]]
            logger.info(f"Reranking: {len(docs)} docs -> top {len(reranked)}")
            return reranked
        else:
            logger.warning("Reranking parse failed, returning original order")
            return docs[:top_n]

    except Exception as e:
        logger.warning(f"Reranking failed, returning original order: {e}")
        return docs[:top_n]


def query_knowledge_base(query: str, k: int = 3, llm=None) -> str:
    """
    Enhanced RAG pipeline with query rewriting and reranking.

    Pipeline:
    1. Query Rewriting -> multiple search queries
    2. Multi-query Retrieval -> broader document recall
    3. Deduplication -> remove repeated documents
    4. LLM Reranking -> precision ranking by relevance
    """
    try:
        db = get_vector_store()

        # Stage 1: Query Rewriting (if LLM is available)
        if llm is not None:
            queries = rewrite_query(query, llm)
        else:
            queries = [query]

        # Stage 2: Multi-query Retrieval
        all_docs = []
        retrieve_k = k * 2 if llm is not None else k  # Over-retrieve for reranking
        for q in queries:
            results = db.similarity_search(q, k=retrieve_k)
            all_docs.extend(results)

        # Stage 3: Deduplication
        unique_docs = deduplicate_docs(all_docs)
        logger.info(f"Retrieved {len(all_docs)} docs, {len(unique_docs)} unique")

        if not unique_docs:
            return "No relevant historical data found."

        # Stage 4: LLM Reranking (if LLM is available)
        if llm is not None and len(unique_docs) > k:
            final_docs = rerank_documents(query, unique_docs, llm, top_n=k)
        else:
            final_docs = unique_docs[:k]

        # Format results
        context_str = ""
        for idx, doc in enumerate(final_docs):
            source = doc.metadata.get("source", "Unknown")
            context_str += f"\n--- Reference {idx + 1} (Source: {source}) ---\n{doc.page_content}\n"

        return context_str

    except Exception as e:
        logger.error(f"RAG retrieval error: {e}")
        return "No relevant historical data found (Retrieval system failure)."
