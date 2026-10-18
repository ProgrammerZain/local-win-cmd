# Learning Roadmap: Local-First RAG, Vector DBs, Data Isolation, and Agent Engineering

## Project Overview

A hands-on, incremental learning project built in Python on a local Windows machine. 

### Core Philosophy
* **One chapter at a time:** One core concept, one clean working implementation, tested in Windows PowerShell, committed to Git.
* **Local-first & Resource-conscious:** Tailored specifically for an Intel Core i5-7200U (2 cores, 4 threads, 2.50 GHz), 16 GB RAM, Intel HD Graphics 620, running Windows-native tools without Docker or cloud lock-in.
* **No black boxes:** Understand the exact mechanics—from raw vectors and distance metrics to application-enforced security boundaries and deterministic agent control loops.

---

## Hardware Budget & Resource Profiles

| Component | Technology | Footprint (RAM / Disk) | Execution Target | Local Service Required |
| :--- | :--- | :--- | :--- | :--- |
| **Document Store** | JSON / SQLite | < 10 MB RAM, < 5 MB Disk | Embedded Python process | None |
| **Embeddings** | `all-MiniLM-L6-v2` | ~250 MB RAM, ~90 MB Disk | CPU (PyTorch / ONNX) | None (in-process) |
| **Vector Index** | Chroma / SQLite-vec | ~50 MB RAM, < 20 MB Disk | CPU (in-process) | None |
| **LLM Inference** | `qwen2.5:1.5b` via Ollama | ~1.5 GB RAM, ~1 GB Disk | CPU (Ollama engine) | `ollama` background service |
| **API Server** | FastAPI / Uvicorn | ~30 MB RAM | CPU | None (single process) |
| **Frontend** | React (Vite) | ~40 MB RAM (dev server) | Node.js (Vite) | `npm run dev` |

*Total concurrent RAM footprint:* ~2.0 GB — well within the 16 GB system memory, leaving ample headroom for Windows and IDEs.

---

## Directory Organization Strategy

```text
local-win-cmd/
│
├── .learning_data/           # LOCAL ONLY (in .gitignore): persistent vector index, SQLite DBs
│   ├── vector_store/         # Persisted Chroma / vector indices
│   └── app.db                # SQLite application database
│
├── docs/                     # IN GIT: Chapter architecture docs and checklists
│   ├── chapter_01.md
│   ├── chapter_02.md
│   └── ...
│
├── src/                      # Source code modularized by chapter progress
│   └── ...
│
├── .gitignore                # Excludes .venv/, .learning_data/, *.db, caches
├── ROADMAP.md                # Project curriculum and roadmap (this file)
├── windows_commands.json     # Knowledge base documents
└── rag_cli.py                # Preserved Chapter 1 baseline
```

---

## Curriculum: Chapter by Chapter

### [Completed] Chapter 1 — Basic RAG Fundamentals
* **Objective:** Understand how an LLM can answer questions using external documents without retraining.
* **Concepts:** Document loading, dense embeddings, vector similarity search, prompt augmentation, generative completion.
* **Working Code:** [`rag_cli.py`](rag_cli.py), [`windows_commands.json`](windows_commands.json).
* **Git Checkpoint:** `e533c85 Chapter 1: basic rag program`

---

### [Next] Chapter 2 — Persistence and Embedding Reuse
* **Objective:** Stop regenerating embeddings on every script startup; understand model loading vs. vector persistence.
* **Prerequisites:** Chapter 1.
* **Concepts:**
  * Model downloading (disk cache) vs. model initialization (RAM) vs. inference (CPU).
  * Document embeddings (static, precomputed) vs. query embeddings (dynamic, per-request).
  * Persisting a vector index to `.learning_data/vector_store`.
  * Incremental loading: detecting when the index exists on disk to skip re-indexing.
  * Benchmarking startup latency with and without persistence.
* **Git Checkpoint:** `Chapter 2: persistent vector storage and embedding reuse`

---

### Chapter 3 — Chunking, Retrieval Quality, and RAG Evaluation
* **Objective:** Move beyond 4 static documents to realistic chunking, similarity scoring, and evaluation.
* **Prerequisites:** Chapter 2.
* **Concepts:**
  * Chunk size, chunk overlap, and boundary splitting.
  * Cosine distance vs. L2 distance vs. inner product.
  * Top-$k$ tuning and similarity score thresholds.
  * Preventing hallucinations: forcing the LLM to refuse when confidence is below threshold.
  * Building a mini automated evaluation test set in Python.
* **Git Checkpoint:** `Chapter 3: chunking strategies, similarity thresholds, and evaluation`

---

### Chapter 4 — SQLite and Persistent Application Data
* **Objective:** Store structured application state in SQLite; distinguish relational data from vector data.
* **Prerequisites:** Chapter 3.
* **Concepts:**
  * When to use relational tables vs. vector embeddings.
  * Python standard library `sqlite3` (no external server required).
  * Creating tables, primary keys, foreign keys, and indexes.
  * Storing user records, document metadata, and execution logs in `.learning_data/app.db`.
* **Git Checkpoint:** `Chapter 4: structured application data with sqlite3`

---

### Chapter 5 — Two Users, Two Knowledge Bases, and Data Isolation
* **Objective:** Build multi-tenant security where User 1 and User 2 cannot access each other's data.
* **Prerequisites:** Chapter 4.
* **Concepts:**
  * Why prompt instructions ("Please ignore User 2's data") are NOT security boundaries.
  * Enforcing data isolation in application logic before vector retrieval occurs.
  * Architectural comparison: Single DB with `user_id` foreign keys vs. multi-tenant SQLite files.
  * Vector index isolation: Isolated collections vs. strict pre-filtering metadata predicates.
  * Automated testing for data leakage and unauthorized cross-tenant queries.
* **Git Checkpoint:** `Chapter 5: multi-tenant data isolation and pre-retrieval authorization`

---

### Chapter 6 — Local Models and Model Abstraction
* **Objective:** Decouple application logic from specific model providers and understand local LLM constraints.
* **Prerequisites:** Chapter 5.
* **Concepts:**
  * Embedding models vs. autoregressive generative LLMs.
  * Quantization (GGUF, Q4_K_M vs. Q8_0) and CPU inference performance.
  * Managing Ollama processes, memory usage, and context window sizing.
  * Writing a provider-agnostic model wrapper interface in Python.
* **Git Checkpoint:** `Chapter 6: model abstraction and local runtime management`

---

### Chapter 7 — RAG Pipeline Observability and Debugging
* **Objective:** Inspect and trace every stage of RAG execution to debug retrieval and generation failures.
* **Prerequisites:** Chapter 6.
* **Concepts:**
  * The 9-stage RAG lifecycle: User Input -> Auth Filter -> Query Embed -> Retrieval -> Context Pack -> Prompt Build -> Model Inference -> Output Filter -> Response.
  * Implementing lightweight, privacy-preserving structured logging.
  * Diagnosing failure modes: Retrieval miss vs. prompt truncation vs. LLM refusal vs. hallucination.
* **Git Checkpoint:** `Chapter 7: pipeline observability and stage-by-stage tracing`

---

### Chapter 8 — Deterministic Tools to LLM Tool Calling
* **Objective:** Enable the system to take deterministic actions via tool calling.
* **Prerequisites:** Chapter 7.
* **Concepts:**
  * Ordinary Python functions vs. JSON schema tool definitions.
  * Tool calling mechanics: How the model outputs structured tool calls instead of conversational text.
  * Executing safe local tools: User profile lookup, knowledge base search, and calculator.
  * Validating tool arguments deterministically before execution.
* **Git Checkpoint:** `Chapter 8: structured tool calling and schema validation`

---

### Chapter 9 — Autonomous Agents and Control Loops
* **Objective:** Build an autonomous agent control loop from first principles.
* **Prerequisites:** Chapter 8.
* **Concepts:**
  * The ReAct loop (Reason -> Act -> Observe -> Repeat).
  * State tracking, memory management, and iteration bounds (max steps).
  * Stopping conditions and safe exit strategies.
  * Handling tool errors gracefully and self-correcting.
* **Git Checkpoint:** `Chapter 9: autonomous react agent loop with iteration safety`

---

### Chapter 10 — Harness Engineering and Production Reliability
* **Objective:** Build the harness software that makes AI systems reliable, predictable, and robust.
* **Prerequisites:** Chapter 9.
* **Concepts:**
  * Defensive harness engineering: Timeouts, memory caps, token budgeting.
  * Output validation with Pydantic schemas.
  * Retry policies with exponential backoff.
  * Regression test harness for deterministic and non-deterministic components.
* **Git Checkpoint:** `Chapter 10: harness engineering, validation, and test harness`

---

### Chapter 11 — Local API and Minimal React Frontend
* **Objective:** Connect the local Python backend to a clean web UI without compromising isolation.
* **Prerequisites:** Chapter 10.
* **Concepts:**
  * Building a lightweight FastAPI backend exposing clean REST endpoints.
  * Why React must never connect directly to the vector store or SQLite.
  * Managing active user context and session headers.
  * Streaming responses, loading states, and error toasts.
* **Git Checkpoint:** `Chapter 11: fastapi backend and minimal react interface`

---

### Chapter 12 — Testing, Hardening, and Production Readiness Checklist
* **Objective:** Perform security audits, regression tests, and prepare a deployment review.
* **Prerequisites:** Chapter 11.
* **Concepts:**
  * Multi-user adversarial testing (prompt injection, tenant traversal).
  * Vector index backup and schema migrations.
  * Performance profiling on CPU-bound hardware.
  * Comprehensive review of what separates a local learning prototype from production.
* **Git Checkpoint:** `Chapter 12: security hardening, regression tests, and final audit`
