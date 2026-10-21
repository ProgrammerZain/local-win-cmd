import time
import ollama
from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.documents import Document

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

SCRIPT_DIR = Path(__file__).resolve().parent
DB_DIR = SCRIPT_DIR / "isolated_store"

USERS = {
    1: {"name": "Zain Irfan", "role": "Owner"},
    2: {"name": "Guest User", "role": "Visitor"},
}

# 1. Initialize embeddings & vector store
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def setup_isolated_data():
    if DB_DIR.exists() and any(DB_DIR.iterdir()):
        return Chroma(persist_directory=str(DB_DIR), embedding_function=embeddings)

    print("[INIT] Seeding isolated documents for User 1 and User 2...")
    
    # User 1 private knowledge: knows their name
    doc_user_1 = Document(
        page_content="User profile: The active user's full name is Zain Irfan, Lead Engineer.",
        metadata={"user_id": 1}
    )

    # User 2 private knowledge: knows about zainbhai command
    doc_user_2 = Document(
        page_content="Command reference: zainbhai is a special dummy test command created by Zain Irfan to verify RAG responses.",
        metadata={"user_id": 2}
    )

    store = Chroma.from_documents(
        documents=[doc_user_1, doc_user_2],
        embedding=embeddings,
        persist_directory=str(DB_DIR)
    )
    return store

vector_store = setup_isolated_data()

def ask_user_rag(active_user_id: int, query: str):
    # CRITICAL: Application-level security filter
    # The retriever ONLY searches documents where metadata user_id matches active_user_id
    results_with_scores = vector_store.similarity_search_with_score(
        query=query,
        k=2,
        filter={"user_id": active_user_id}
    )

    # Strict distance threshold guardrail
    valid_docs = [doc for doc, score in results_with_scores if score < 1.35]

    if not valid_docs:
        return "I do not have access to that information in your authorized knowledge base."

    context = "\n---\n".join([doc.page_content for doc in valid_docs])
    prompt = f"""You are a helpful assistant. Based ONLY on the following authorized context, answer the user's question.
If the answer is not contained in the context, say that you do not know.

Authorized Context:
{context}

Question: {query}
Answer:"""

    response = ollama.chat(
        model="qwen2.5:1.5b",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]

def main():
    active_user = 1
    print("\n" + "=" * 50)
    print("  MULTI-TENANT DATA ISOLATION LAB")
    print("=" * 50)

    while True:
        user_info = USERS[active_user]
        print(f"\n[ACTIVE USER]: #{active_user} - {user_info['name']} ({user_info['role']})")
        print("Commands: 'switch' to toggle user | 'exit' to quit")
        query = input("Ask question: ").strip()

        if query.lower() == "exit":
            break
        elif query.lower() == "switch":
            active_user = 2 if active_user == 1 else 1
            print(f"Switched to User #{active_user}")
            continue
        elif not query:
            continue

        answer = ask_user_rag(active_user, query)
        print(f"\nResponse:\n{answer}\n")

if __name__ == "__main__":
    main()
