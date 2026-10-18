# Local AI Learning Lab

Welcome to your self-contained, offline-friendly AI Learning Lab.

This laboratory is designed to help you build a deep, hands-on understanding of LLMs, RAG, vector embeddings, SQLite, multi-tenant data isolation, autonomous agent loops, harness engineering, and frontend integration.

---

## 1. How It Works

* **Self-Guided Learning:** The code for future chapters is **not** pre-written for you. You will implement each chapter yourself following the step-by-step tutorial in each chapter's `README.md`.
* **Zero Cloud Lock-in:** Every chapter runs locally on Windows, using CPU-friendly models (`all-MiniLM-L6-v2`, `qwen2.5:1.5b` via Ollama), standard Python packages, and SQLite.
* **Isolated Learning Data:** The entire `.learning_data/` directory is excluded from Git in `.gitignore`. Your experiments, generated databases, vector stores, and local test artifacts stay local.

---

## 2. Launching the Lab

From the repository root (`E:\GIT_FOR_ZAIN\llm\local-win-cmd`), activate your virtual environment and run:

```powershell
.\.venv\Scripts\activate
python .\.learning_data\main.py
```

The interactive menu will appear:

```text
========================================
       LOCAL AI LEARNING LAB
========================================

Available chapters:

 1. Chapter 1 - Basic RAG (completed)
 2. Chapter 2 - Persistence and Embedding Reuse
 3. Chapter 3 - Chunking and Retrieval Evaluation
 4. Chapter 4 - SQLite Fundamentals
 5. Chapter 5 - Two Users and Data Isolation
 6. Chapter 6 - Local Language Models
 7. Chapter 7 - RAG Debugging and Observability
 8. Chapter 8 - Tools and Tool Calling
 9. Chapter 9 - Agents and Control Loops
10. Chapter 10 - Harness Engineering
11. Chapter 11 - React Integration
12. Chapter 12 - Testing and Hardening

 0. Exit
```

---

## 3. Directory Layout

```text
.learning_data/
│
├── main.py                   # Chapter launcher script
├── README.md                 # This overview guide
│
├── chapter_01/               # Completed baseline
│   ├── README.md             # How Chapter 1 works
│   ├── rag_cli.py            # Preserved copy of Chapter 1 baseline
│   └── windows_commands.json # Preserved copy of knowledge base
│
├── chapter_02/               # Persistence and Embedding Reuse
│   └── README.md
│
├── chapter_03/               # Chunking and Retrieval Evaluation
│   └── README.md
│
├── chapter_04/               # SQLite Fundamentals
│   └── README.md
│
├── chapter_05/               # Two Users and Data Isolation
│   └── README.md
│
├── chapter_06/               # Local Language Models
│   └── README.md
│
├── chapter_07/               # RAG Debugging and Observability
│   └── README.md
│
├── chapter_08/               # Tools and Tool Calling
│   └── README.md
│
├── chapter_09/               # Agents and Control Loops
│   └── README.md
│
├── chapter_10/               # Harness Engineering
│   └── README.md
│
├── chapter_11/               # React Integration
│   └── README.md
│
└── chapter_12/               # Testing and Hardening
    └── README.md
```

---

## 4. How to Complete a Chapter

1. Run `python .\.learning_data\main.py` and select the chapter number to inspect the guide.
2. Read the chapter's `README.md` thoroughly. Understand the **Objective**, **Concepts**, and **Architecture**.
3. Create the required file (e.g. `rag_persistent.py`) inside that chapter's folder.
4. Follow the step-by-step tasks and write the code manually.
5. Run the manual tests and experiments in PowerShell.
6. Verify against the checklist.
7. Return to `main.py` and run your newly created script.
