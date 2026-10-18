import json
import ollama
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# 1. Load your command dataset
with open("windows_commands.json", "r") as f:
    commands_data = json.load(f)

docs = [
    Document(
        page_content=f"Task: {item['task']}\nBash equivalent: {item['bash']}\nCMD: {item['cmd']}\nPowerShell: {item['powershell']}\nNotes: {item['notes']}",
        metadata={"task": item["task"]}
    )
    for item in commands_data
]

# 2. Local embeddings (runs fast on CPU)
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 3. In-memory or local persistent vector store
vector_store = Chroma.from_documents(docs, embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 2})

def ask_rag(query: str):
    # Retrieve top matched commands
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
    return response["message"]["content"]

# Interactive test loop
if __name__ == "__main__":
    while True:
        user_query = input("\nAsk command (e.g. 'how to see hidden files like ls -a') [or 'exit']: ")
        if user_query.strip().lower() == "exit":
            break
        print("\n" + ask_rag(user_query))
