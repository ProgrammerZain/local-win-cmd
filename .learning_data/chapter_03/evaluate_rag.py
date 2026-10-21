"""
Chapter 3: Chunking, Retrieval Quality, and RAG Evaluation
Local IT Support Knowledge Assistant.

Uses:
- Ollama embeddings: nomic-embed-text
- Local generation: qwen2.5:3b
- Chroma with cosine distance
- JSON knowledge-base articles split into overlapping chunks

Run from the repository root:
    python .\.learning_data\chapter_03\evaluate_rag.py

The index is stored under this chapter's eval_store directory. It is rebuilt only
when the source data or chunking/model configuration changes.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

SCRIPT_DIR = Path(__file__).resolve().parent
DATA_FILE = SCRIPT_DIR / "knowledge_base.json"
DB_DIR = SCRIPT_DIR / "eval_store"
MANIFEST_FILE = DB_DIR / "index_manifest.json"

EMBEDDING_MODEL = "nomic-embed-text"
GENERATION_MODEL = "qwen2.5:3b"
CHUNK_SIZE = 650
CHUNK_OVERLAP = 100

# Chroma's cosine distance: smaller is more similar.
# Tune this using the distances printed by your own machine/model.
# You can override it in PowerShell:
# $env:RAG_DISTANCE_THRESHOLD = "0.55"
DISTANCE_THRESHOLD = float(__import__("os").environ.get("RAG_DISTANCE_THRESHOLD", "0.55"))

TEST_CASES = [
    {
        "query": "My laptop is connected to Wi-Fi, but no websites load. What should I check first?",
        "should_find": True,
        "expected_article": "NET-001",
    },
    {
        "query": "How can I diagnose a DNS resolution failure and clear a stale DNS cache?",
        "should_find": True,
        "expected_article": "NET-002",
    },
    {
        "query": "The printer says online, but print jobs stay in the queue. What should I inspect?",
        "should_find": True,
        "expected_article": "PRN-001",
    },
    {
        "query": "My Windows system drive is almost full and updates are failing. What is a safe first step?",
        "should_find": True,
        "expected_article": "WIN-001",
    },
    {
        "query": "My Python program cannot connect to the local Ollama service. How should I debug it?",
        "should_find": True,
        "expected_article": "DEV-001",
    },
    {
        "query": "Give me a chocolate cake recipe with chocolate frosting.",
        "should_find": False,
        "expected_article": None,
    },
    {
        "query": "Explain the causes of the French Revolution.",
        "should_find": False,
        "expected_article": None,
    },
    {
        "query": "What are the best exercises for training a pet parrot?",
        "should_find": False,
        "expected_article": None,
    },
]


def load_articles() -> list[dict[str, Any]]:
    with DATA_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list) or not data:
        raise ValueError(f"{DATA_FILE.name} must contain a non-empty JSON list.")
    return data


def make_documents(articles: list[dict[str, Any]]) -> list[Document]:
    documents: list[Document] = []

    for article in articles:
        content = (
            f"Article ID: {article['id']}\n"
            f"Title: {article['title']}\n"
            f"Category: {article['category']}\n"
            f"Symptoms:\n" + "\n".join(f"- {x}" for x in article["symptoms"]) + "\n"
            f"Diagnosis:\n" + "\n".join(f"- {x}" for x in article["diagnosis"]) + "\n"
            f"Resolution:\n" + "\n".join(f"- {x}" for x in article["resolution"]) + "\n"
            f"Cautions:\n" + "\n".join(f"- {x}" for x in article["cautions"])
        )
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "article_id": article["id"],
                    "title": article["title"],
                    "category": article["category"],
                    "source_url": article.get("source_url", ""),
                },
            )
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        add_start_index=True,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(documents)

    # Add stable identifiers to help us understand which article/chunk was retrieved.
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_number"] = index
    return chunks


def configuration_fingerprint(articles: list[dict[str, Any]]) -> str:
    """Change the index when source data or embedding/chunk settings change."""
    payload = {
        "articles": articles,
        "embedding_model": EMBEDDING_MODEL,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "splitter": "RecursiveCharacterTextSplitter-v1",
    }
    encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def load_or_build_store(chunks: list[Document], fingerprint: str, embeddings: OllamaEmbeddings) -> Chroma:
    DB_DIR.mkdir(parents=True, exist_ok=True)

    existing_fingerprint = None
    if MANIFEST_FILE.exists():
        try:
            existing_fingerprint = json.loads(MANIFEST_FILE.read_text(encoding="utf-8")).get("fingerprint")
        except (json.JSONDecodeError, OSError):
            existing_fingerprint = None

    if existing_fingerprint == fingerprint:
        try:
            store = Chroma(
                collection_name="it_support_chapter_03",
                embedding_function=embeddings,
                persist_directory=str(DB_DIR),
                collection_metadata={"hnsw:space": "cosine"},
            )
            if store._collection.count() > 0:
                print(f"[INFO] Reusing persisted index ({store._collection.count()} chunks).")
                return store
        except Exception as exc:
            print(f"[WARN] Could not reuse saved index ({exc}). Rebuilding it.")

    if DB_DIR.exists():
        shutil.rmtree(DB_DIR)
    DB_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Building index for {len(chunks)} chunks. This embeds the documents.")
    ids = []
    for index, chunk in enumerate(chunks):
        raw = f"{chunk.metadata.get('article_id')}|{chunk.metadata.get('start_index')}|{index}|{chunk.page_content}"
        ids.append(hashlib.sha256(raw.encode("utf-8")).hexdigest())

    store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        ids=ids,
        collection_name="it_support_chapter_03",
        persist_directory=str(DB_DIR),
        collection_metadata={"hnsw:space": "cosine"},
    )
    MANIFEST_FILE.write_text(
        json.dumps({"fingerprint": fingerprint, "chunks": len(chunks)}, indent=2),
        encoding="utf-8",
    )
    return store


def answer_question(llm: ChatOllama, query: str, doc: Document) -> str:
    prompt = f"""You are a local IT support assistant.
Answer the user's question using only the supplied knowledge-base excerpt.
If the excerpt does not contain enough information, say what is missing instead
of inventing instructions. Do not claim to have run commands or inspected the PC.
Give concise, ordered troubleshooting steps and mention relevant cautions.

Knowledge-base excerpt:
Title: {doc.metadata.get('title', 'Unknown')}
Category: {doc.metadata.get('category', 'Unknown')}
{doc.page_content}

User question: {query}
"""
    response = llm.invoke(prompt)
    return str(response.content).strip()


def main() -> int:
    started = time.perf_counter()

    try:
        articles = load_articles()
        chunks = make_documents(articles)
        print(f"[INFO] Loaded {len(articles)} articles and split them into {len(chunks)} chunks.")
        print(f"[INFO] Embedding model: {EMBEDDING_MODEL}")
        print(f"[INFO] Generation model: {GENERATION_MODEL}")
        print(f"[INFO] Cosine-distance threshold: {DISTANCE_THRESHOLD:.3f}")

        embeddings = OllamaEmbeddings(model=EMBEDDING_MODEL)
        store = load_or_build_store(chunks, configuration_fingerprint(articles), embeddings)
        llm = ChatOllama(model=GENERATION_MODEL, temperature=0)

    except FileNotFoundError as exc:
        print(f"[ERROR] Required file not found: {exc}")
        return 1
    except Exception as exc:
        print(f"[ERROR] Setup failed: {exc}")
        print("Check that Ollama is running and both model names exist in `ollama list`.")
        print("Required packages: langchain-chroma, langchain-ollama, langchain-text-splitters.")
        return 1

    print(f"[INFO] Setup completed in {time.perf_counter() - started:.2f}s.")
    print("\nRunning retrieval evaluation\n" + "=" * 72)

    passed = 0
    for number, case in enumerate(TEST_CASES, start=1):
        query = case["query"]
        results = store.similarity_search_with_score(query, k=3)

        if not results:
            print(f"\n[{number}] {query}\n  No results returned.")
            continue

        best_doc, best_distance = results[0]
        accepted = best_distance <= DISTANCE_THRESHOLD
        expected = case["should_find"]
        retrieval_pass = accepted == expected
        if retrieval_pass:
            passed += 1

        print(f"\n[{number}] {query}")
        print(f"  Best article: {best_doc.metadata.get('article_id')} — {best_doc.metadata.get('title')}")
        print(f"  Cosine distance: {best_distance:.4f}")
        print(f"  Threshold decision: {'ACCEPT' if accepted else 'REFUSE'}")
        print(f"  Expected relevant: {expected} -> [{'PASS' if retrieval_pass else 'FAIL'}]")

        if accepted:
            try:
                answer = answer_question(llm, query, best_doc)
                print("  Answer:")
                print("  " + answer.replace("\n", "\n  "))
                print(f"  Reference: {best_doc.metadata.get('source_url', '')}")
            except Exception as exc:
                print(f"  [GENERATION ERROR] {exc}")
        else:
            print("  Answer: I could not find sufficiently relevant information in the local knowledge base.")

        if expected and case.get("expected_article"):
            actual_id = best_doc.metadata.get("article_id")
            print(
                f"  Expected article: {case['expected_article']} "
                f"(top article match: {'YES' if actual_id == case['expected_article'] else 'NO'})"
            )

    print("\n" + "=" * 72)
    print(f"Retrieval classification: {passed}/{len(TEST_CASES)} passed.")
    print("Note: retrieval PASS checks the relevance/refusal decision, not factual answer quality.")
    print("Review distances and answers. Tune RAG_DISTANCE_THRESHOLD based on your own results.")
    print("If you edit knowledge_base.json or chunk/model settings, the index will be rebuilt.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
