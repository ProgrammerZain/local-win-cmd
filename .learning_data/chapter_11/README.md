# Chapter 11: Python API and Minimal React Frontend Integration

## 1. Learning Objectives
* Understand the architectural boundary between a **Web Frontend (React)** and a **Local Backend (FastAPI)**.
* Learn why a browser must **NEVER** connect directly to a vector database or SQLite file.
* Build a lightweight REST API in Python using FastAPI exposing `/ask` and `/users` endpoints.
* Understand the security reality: A user ID chosen in a frontend dropdown is **development simulation**, not true authentication.

---

## 2. Core Concepts to Master

### Why React Cannot Touch the Database Directly
1. **Network & File Boundaries:** React runs in the user's browser sandbox (JavaScript). It has no access to Windows filesystem files like `app.db` or `.learning_data/chapter_02/vector_store`.
2. **Security & Secrets:** If a frontend connected directly to a vector database, an attacker could open Chrome DevTools, inspect the network packets, and dump every other user's private embeddings.
3. **The API as Gateway:** FastAPI acts as the strict gatekeeper. It validates sessions, injects authorization filters, computes vectors on the host machine, and only returns sanitized text.

---

## 3. Architecture Overview

```mermaid
flowchart LR
    subgraph BrowserSandbox [Browser Sandbox (React)]
        UI[User Question Input + User Switcher] --> Fetch[fetch('/api/ask')]
    end

    subgraph HostMachine [Python Host Machine]
        Fetch --> API[FastAPI Server on :8000]
        API --> Auth[Validate User ID & Inject Filter]
        Auth --> VStore[(Chroma / SQLite)]
        VStore --> LLM[Ollama Local Engine]
        LLM --> Res[JSON: {answer: ...}]
    end

    Res --> UI
```

---

## 4. Files You Will Eventually Create
Inside `.learning_data/chapter_11/`:
* `api_server.py`: FastAPI server exposing `/api/ask` and `/api/users`.
* `frontend/`: Minimal React + Vite application (or single-page HTML/JS demo) for testing.

---

## 5. Step-by-Step Implementation Guide

### Step 5.1: Create `api_server.py`
Create `.learning_data/chapter_11/api_server.py`:

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Local AI RAG API")

# Enable CORS for local web dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    user_id: int
    query: str

class QueryResponse(BaseModel):
    user_id: int
    query: str
    answer: str
    duration_ms: float

@app.get("/api/users")
def get_users():
    return [
        {"id": 1, "name": "Zain Irfan", "role": "Owner"},
        {"id": 2, "name": "Guest User", "role": "Visitor"},
    ]

@app.post("/api/ask", response_model=QueryResponse)
def ask_question(req: QueryRequest):
    if req.user_id not in (1, 2):
        raise HTTPException(status_code=403, detail="Unauthorized user.")

    # In actual integration, calls your isolated RAG function from Chapter 5
    if req.user_id == 1 and "name" in req.query.lower():
        ans = "Your name is Zain Irfan."
    elif req.user_id == 2 and "zainbhai" in req.query.lower():
        ans = "zainbhai is a test dummy command created by Zain Irfan."
    else:
        ans = "I do not have access to that information in your authorized knowledge base."

    return QueryResponse(
        user_id=req.user_id,
        query=req.query,
        answer=ans,
        duration_ms=45.2
    )

if __name__ == "__main__":
    import uvicorn
    print("\nStarting local FastAPI server at http://127.0.0.1:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

---

## 6. PowerShell Commands to Test

Run the API:
```powershell
python .\.learning_data\chapter_11\api_server.py
```

Test with PowerShell `Invoke-RestMethod` (no React needed to verify the API):
```powershell
# Test User 1
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/ask" -Method Post -ContentType "application/json" -Body '{"user_id": 1, "query": "What is my name?"}'

# Test User 2 denied access to User 1's secret
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/ask" -Method Post -ContentType "application/json" -Body '{"user_id": 2, "query": "What is my name?"}'
```

---

## 7. Verification Checklist
- [ ] Created `api_server.py`.
- [ ] Verified that endpoints `/api/users` and `/api/ask` respond with proper JSON.
- [ ] Verified cross-user isolation via REST requests.

---

## 8. Bridge to Chapter 12
You have built the entire stack! The final milestone is **Chapter 12: Testing, Hardening, and Production Readiness**.
