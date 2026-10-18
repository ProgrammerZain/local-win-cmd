import os
import json
import time
import ollama
from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Try modern import first, fallback to community
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings

# Define paths relative to this script
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DB_DIR = SCRIPT_DIR / "vector_store"
DOCS_FILE = REPO_ROOT / "windows_commands.json"

print(f"[INIT] Vector Store Directory: {DB_DIR}")

# 1. Initialize local embedding model
t0 = time.perf_counter()
print("[INFO] Loading embedding model into RAM...")
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
print(f"[DONE] Model loaded in {time.perf_counter() - t0:.2f}s")

# 2. Check if persistent vector store already exists
if not DB_DIR.exists() or not any(DB_DIR.iterdir()):
    print("\n[COLD START] No persistent index found. Embedding documents from scratch...")
    t_index = time.perf_counter()
    
    with open(DOCS_FILE, "r", encoding="utf-8") as f:
        commands_data = json.load(f)

    docs = [
        Document(
            page_content=f"Category: {item['category']}\nKeywords: {', '.join(item['keywords'])}\nAction: {item['action']}\nBash equivalent: {item['bash']}\nWindows CMD: {item['windows_cmd']}\nPowerShell: {item['powershell']}\nNotes: {item['context_notes']}",
            metadata={"action": item["action"]}
        )
        for item in commands_data
    ]

    vector_store = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        persist_directory=str(DB_DIR)
    )
    print(f"[COLD START] Indexed {len(docs)} documents in {time.perf_counter() - t_index:.2f}s")
else:
    print("\n[WARM START] Persistent index found on disk! Reusing existing embeddings...")
    t_load = time.perf_counter()
    vector_store = Chroma(
        persist_directory=str(DB_DIR),
        embedding_function=embeddings
    )
    print(f"[WARM START] Vector store loaded in {time.perf_counter() - t_load:.4f}s (No re-embedding!)")

retriever = vector_store.as_retriever(search_kwargs={"k": 2})

def ask_rag(query: str):
    t_query = time.perf_counter()
    results = retriever.invoke(query)
    context = "\n---\n".join([doc.page_content for doc in results])
    
    prompt = f"""You are a Windows CLI assistant. Based ONLY on the following context, answer the user's question with the exact Windows CMD and PowerShell commands.

Context:
{context}

Question: {query}
Answer:"""

    response = ollama.chat(
        model="qwen2.5:1.5b",
        messages=[{"role": "user", "content": prompt}]
    )
    duration = time.perf_counter() - t_query
    return response["message"]["content"], duration

if __name__ == "__main__":
    print("\nReady! Ask questions or type 'exit'.")
    while True:
        query = input("\nAsk command: ")
        if query.strip().lower() == "exit":
            break
        answer, dur = ask_rag(query)
        print(f"\n{answer}\n(Answered in {dur:.2f}s)")
