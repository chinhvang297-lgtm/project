# /Users/shanzi/iemsProject/app/tools/retriever.py
import os
from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings

PERSIST_DIRECTORY = "./nba_knowledge_db"

def get_vector_store():
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise ValueError("DASHSCOPE_API_KEY not found in environment variables")

    embeddings = DashScopeEmbeddings(
        model="text-embedding-v1",
        dashscope_api_key=api_key
    )

    vector_db = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=embeddings,
        collection_name="nba_history"
    )
    return vector_db

def query_knowledge_base(query: str, k: int = 3):
    try:
        db = get_vector_store()

        results = db.similarity_search(query, k=k)

        context_str = ""
        for idx, doc in enumerate(results):
            source = doc.metadata.get("source", "Unknown")
            context_str += f"\n--- Reference {idx + 1} (Source: {source}) ---\n{doc.page_content}\n"

        if not context_str:
            return "No relevant historical data found."

        return context_str
    except Exception as e:
        print(f"RAG retrieval error: {e}")
        return "No relevant historical data found (Retrieval system failure)."