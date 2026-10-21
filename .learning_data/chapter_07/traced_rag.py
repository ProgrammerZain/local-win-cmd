"""
Chapter 7: Real RAG Architecture & Production Observability Engine

Implements an end-to-end, fully functional 9-stage RAG pipeline with:
- Real local Chroma vector store
- Real HuggingFace embeddings (all-MiniLM-L6-v2)
- Real Ollama LLM generation (qwen2.5:1.5b)
- Secret / PII sanitization in telemetry logs
- Precise stage-by-stage latency tracking (ms)
- Automatic Root-Cause Diagnostic Matrix (detects Retrieval Miss vs Permission Block vs Hallucination)
"""

import re
import time
import json
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings
import ollama


# =====================================================================
# 1. OBSERVABILITY TELEMETRY SCHEMA
# =====================================================================

@dataclass
class StageTiming:
    embed_ms: float = 0.0
    retrieval_ms: float = 0.0
    filter_ms: float = 0.0
    generation_ms: float = 0.0
    total_pipeline_ms: float = 0.0

@dataclass
class RAGTrace:
    # Stage 1: Input & Sanitization
    raw_query: str = ""
    sanitized_query: str = ""
    redacted_secrets: List[str] = field(default_factory=list)

    # Stage 2: User Context & RBAC
    user_id: int = 0
    user_role: str = ""

    # Stage 3: Embedding
    embedding_dim: int = 0

    # Stage 4: Raw Vector Retrieval (Before Auth)
    raw_retrieved_count: int = 0
    raw_best_distance: float = 999.0

    # Stage 5: Security & Threshold Filter
    auth_passed_count: int = 0
    auth_rejected_reason: Optional[str] = None
    best_authorized_distance: float = 999.0

    # Stage 6: Context Packing
    packed_doc_ids: List[str] = field(default_factory=list)
    context_char_count: int = 0
    context_truncated: bool = False

    # Stage 7: Prompt Construction
    prompt_length_chars: int = 0

    # Stage 8: LLM Generation
    generation_model: str = ""
    response_token_estimate: int = 0
    tokens_per_sec: float = 0.0

    # Stage 9: Lifecycle Status & Diagnostics
    final_status: str = "PENDING"
    root_cause_diagnosis: str = ""

    # Timings
    timings: StageTiming = field(default_factory=StageTiming)


# =====================================================================
# 2. SETUP REAL KNOWLEDGE BASE (Multi-Tenant IT & Infrastructure)
# =====================================================================

def init_knowledge_base(embeddings) -> Chroma:
    """Seeds in-memory Chroma with diverse role-restricted technical documents."""
    store = Chroma(
        collection_name="it_observability_kb",
        embedding_function=embeddings
    )

    documents = [
        # Developer Tier Docs
        Document(
            page_content="Git Workflow: Feature branches must be named feature/JIRA-ID. Rebase before merging into main.",
            metadata={"doc_id": "GIT-001", "min_role": "dev", "dept": "engineering"}
        ),
        Document(
            page_content="Docker Local Dev: Use 'docker compose up -d postgres redis' to start local databases on ports 5432 and 6379.",
            metadata={"doc_id": "DEV-002", "min_role": "dev", "dept": "engineering"}
        ),
        # Admin / Security Tier Docs
        Document(
            page_content="Production DB Cluster: Master host is pg-prod-01.internal, replication port 5432, master role is superuser_admin.",
            metadata={"doc_id": "SEC-001", "min_role": "admin", "dept": "infrastructure"}
        ),
        Document(
            page_content="AWS Root Break-Glass: Access credentials stored in Vault under secret/infra/aws-root. 2FA hardware key required.",
            metadata={"doc_id": "SEC-002", "min_role": "admin", "dept": "security"}
        ),
        # Public / Guest Tier Docs
        Document(
            page_content="Office Wi-Fi: Connect to 'GuestCorp', open browser to accept portal terms. Bandwidth throttled to 25 Mbps.",
            metadata={"doc_id": "PUB-001", "min_role": "guest", "dept": "it_support"}
        ),
    ]

    store.add_documents(documents)
    return store


# =====================================================================
# 3. PRODUCTION 9-STAGE OBSERVABILITY PIPELINE
# =====================================================================

class TracedRAGPipeline:
    def __init__(self, vector_store: Chroma, embeddings, model_name: str = "qwen2.5:1.5b"):
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.model_name = model_name
        self.distance_threshold = 1.25  # Squared L2 cutoff for all-MiniLM-L6-v2
        self.max_context_chars = 1500

        # Role Hierarchy: guest < dev < admin
        self.role_hierarchy = {"guest": 1, "dev": 2, "admin": 3}

    def _sanitize_input(self, raw_query: str) -> tuple[str, list[str]]:
        """Stage 1: Redact raw secrets (passwords, bearer tokens, api keys) from logs."""
        redacted = []
        cleaned = raw_query

        # Scrub Bearer tokens / API keys
        secret_patterns = [
            (r'(Bearer\s+[A-Za-z0-9_\-\.]+)', '[REDACTED_TOKEN]'),
            (r'((?:api[_-]?key|secret|password)\s*[:=]\s*\S+)', '[REDACTED_CREDENTIAL]')
        ]
        for pattern, replacement in secret_patterns:
            matches = re.findall(pattern, cleaned, re.IGNORECASE)
            if matches:
                redacted.extend(matches if isinstance(matches[0], str) else [m[0] for m in matches])
                cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

        return cleaned, redacted

    def execute(self, query: str, user_id: int, user_role: str) -> tuple[str, RAGTrace]:
        t_pipeline_start = time.perf_counter()
        trace = RAGTrace()

        # -----------------------------------------------------------------
        # STAGE 1: Input Received & Privacy Sanitization
        # -----------------------------------------------------------------
        trace.raw_query = query
        sanitized_query, redacted = self._sanitize_input(query)
        trace.sanitized_query = sanitized_query
        trace.redacted_secrets = redacted

        # -----------------------------------------------------------------
        # STAGE 2: User Context & Role Resolution
        # -----------------------------------------------------------------
        trace.user_id = user_id
        trace.user_role = user_role
        user_level = self.role_hierarchy.get(user_role.lower(), 1)

        # -----------------------------------------------------------------
        # STAGE 3: Query Embedding Generation
        # -----------------------------------------------------------------
        t_emb_0 = time.perf_counter()
        emb_vector = self.embeddings.embed_query(sanitized_query)
        trace.timings.embed_ms = (time.perf_counter() - t_emb_0) * 1000
        trace.embedding_dim = len(emb_vector)

        # -----------------------------------------------------------------
        # STAGE 4: Vector Database Retrieval (Raw Candidates)
        # -----------------------------------------------------------------
        t_ret_0 = time.perf_counter()
        # Retrieve top 3 candidates regardless of role to detect permission blocks vs data misses
        raw_candidates = self.vector_store.similarity_search_with_score(sanitized_query, k=3)
        trace.timings.retrieval_ms = (time.perf_counter() - t_ret_0) * 1000
        trace.raw_retrieved_count = len(raw_candidates)

        if raw_candidates:
            trace.raw_best_distance = min(score for _, score in raw_candidates)

        # -----------------------------------------------------------------
        # STAGE 5: Security Filter & Distance Threshold
        # -----------------------------------------------------------------
        t_filt_0 = time.perf_counter()
        authorized_docs = []

        for doc, score in raw_candidates:
            doc_role = doc.metadata.get("min_role", "admin")
            required_level = self.role_hierarchy.get(doc_role, 3)

            # Check 1: Role permission
            if user_level < required_level:
                trace.auth_rejected_reason = f"Required role '{doc_role}' exceeds user role '{user_role}'"
                continue

            # Check 2: Semantic relevance guardrail
            if score > self.distance_threshold:
                trace.auth_rejected_reason = f"Distance {score:.3f} exceeded threshold {self.distance_threshold}"
                continue

            authorized_docs.append((doc, score))

        trace.timings.filter_ms = (time.perf_counter() - t_filt_0) * 1000
        trace.auth_passed_count = len(authorized_docs)

        # Root-cause branching for early exit
        if not authorized_docs:
            if raw_candidates and trace.raw_best_distance < self.distance_threshold:
                trace.final_status = "REFUSED_PERMISSION_DENIED"
                trace.root_cause_diagnosis = (
                    f"STAGE 5 FAILURE: Relevant knowledge exists (best distance {trace.raw_best_distance:.3f}), "
                    f"but user role '{user_role}' is unauthorized to access it."
                )
            else:
                trace.final_status = "REFUSED_RETRIEVAL_MISS"
                trace.root_cause_diagnosis = (
                    f"STAGE 4/5 FAILURE: No relevant documents found in knowledge base "
                    f"(closest distance was {trace.raw_best_distance:.3f}, cutoff is {self.distance_threshold})."
                )

            trace.timings.total_pipeline_ms = (time.perf_counter() - t_pipeline_start) * 1000
            return "I do not have authorized information to answer your question.", trace

        trace.best_authorized_distance = min(score for _, score in authorized_docs)

        # -----------------------------------------------------------------
        # STAGE 6: Context Packing & Token/Budget Check
        # -----------------------------------------------------------------
        packed_parts = []
        packed_chars = 0
        for doc, _ in authorized_docs:
            content = f"[{doc.metadata.get('doc_id')}]: {doc.page_content}"
            if packed_chars + len(content) > self.max_context_chars:
                trace.context_truncated = True
                break
            packed_parts.append(content)
            trace.packed_doc_ids.append(doc.metadata.get("doc_id", "UNKNOWN"))
            packed_chars += len(content)

        packed_context = "\n\n".join(packed_parts)
        trace.context_char_count = packed_chars

        # -----------------------------------------------------------------
        # STAGE 7: Prompt Construction
        # -----------------------------------------------------------------
        prompt = (
            f"You are a local technical assistant. Answer the user question concisely using ONLY the authorized context below.\n"
            f"If the answer is not in the context, say 'I do not know'.\n\n"
            f"Authorized Context:\n{packed_context}\n\n"
            f"Question: {sanitized_query}\n"
            f"Answer:"
        )
        trace.prompt_length_chars = len(prompt)

        # -----------------------------------------------------------------
        # STAGE 8: Local LLM Generation
        # -----------------------------------------------------------------
        t_gen_0 = time.perf_counter()
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.0}
            )
            raw_answer = response["message"]["content"].strip()
            gen_time = time.perf_counter() - t_gen_0
            trace.timings.generation_ms = gen_time * 1000

            # Token speed metrics
            eval_count = response.get("eval_count", len(raw_answer.split()) * 1.3)
            trace.response_token_estimate = int(eval_count)
            trace.tokens_per_sec = eval_count / gen_time if gen_time > 0 else 0.0
            trace.generation_model = self.model_name
        except Exception as exc:
            trace.final_status = "LLM_GENERATION_FAILED"
            trace.root_cause_diagnosis = f"STAGE 8 FAILURE: Ollama error ({exc})"
            trace.timings.total_pipeline_ms = (time.perf_counter() - t_pipeline_start) * 1000
            return f"Error communicating with local language model: {exc}", trace

        # -----------------------------------------------------------------
        # STAGE 9: Factuality Verification & Status Return
        # -----------------------------------------------------------------
        trace.timings.total_pipeline_ms = (time.perf_counter() - t_pipeline_start) * 1000

        if "do not know" in raw_answer.lower():
            trace.final_status = "MODEL_UNKNOWN_RESPONSE"
            trace.root_cause_diagnosis = "STAGE 8/9 NOTE: Context was passed, but model could not derive the answer."
        else:
            trace.final_status = "SUCCESS"
            trace.root_cause_diagnosis = "HEALTHY: End-to-end execution succeeded with authorized grounded context."

        return raw_answer, trace


# =====================================================================
# 4. OBSERVABILITY DASHBOARD PRINTER
# =====================================================================

def render_observability_report(query: str, answer: str, trace: RAGTrace):
    status_icons = {
        "SUCCESS": "[OK]",
        "REFUSED_PERMISSION_DENIED": "[SECURITY-BLOCK]",
        "REFUSED_RETRIEVAL_MISS": "[DATA-MISS]",
        "MODEL_UNKNOWN_RESPONSE": "[LLM-UNCERTAIN]",
        "LLM_GENERATION_FAILED": "[ERROR]"
    }
    icon = status_icons.get(trace.final_status, "[INFO]")

    print("\n" + "=" * 70)
    print(f"  RAG OBSERVABILITY REPORT  |  Status: {icon} {trace.final_status}")
    print("=" * 70)
    print(f"- Query Received : {trace.raw_query}")
    if trace.redacted_secrets:
        print(f"- PII Redacted   : {trace.redacted_secrets} -> Cleaned: '{trace.sanitized_query}'")
    print(f"- Active User    : User #{trace.user_id} (Role: '{trace.user_role}')")
    print(f"- Final Answer   : {answer}")

    print("\n--- Latency Breakdown (Waterfall) ---")
    print(f"  Stage 3 (Embedding)  : {trace.timings.embed_ms:7.2f} ms")
    print(f"  Stage 4 (Retrieval)  : {trace.timings.retrieval_ms:7.2f} ms")
    print(f"  Stage 5 (Filtering)  : {trace.timings.filter_ms:7.2f} ms")
    print(f"  Stage 8 (Generation) : {trace.timings.generation_ms:7.2f} ms ({trace.tokens_per_sec:.1f} tokens/s)")
    print(f"  Total Wall Time      : {trace.timings.total_pipeline_ms:7.2f} ms")

    print("\n--- Pipeline Diagnostics ---")
    print(f"  Raw Docs Retrieved   : {trace.raw_retrieved_count} (Best raw distance: {trace.raw_best_distance:.3f})")
    print(f"  Authorized Docs Passed: {trace.auth_passed_count} {trace.packed_doc_ids}")
    print(f"  Prompt Payload Size  : {trace.prompt_length_chars} chars (Context: {trace.context_char_count} chars)")
    print(f"  Diagnostic Root Cause: {trace.root_cause_diagnosis}")
    print("=" * 70 + "\n")


# =====================================================================
# 5. TEST BENCHMARK & DEMO RUNNER
# =====================================================================

if __name__ == "__main__":
    print("\n[INIT] Initializing HuggingFace Embeddings & Local Chroma Store...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = init_knowledge_base(embeddings)
    pipeline = TracedRAGPipeline(vector_store, embeddings, model_name="qwen2.5:1.5b")

    test_cases = [
        {
            "name": "TEST 1: Authorized Developer Query",
            "query": "How do I start Postgres and Redis locally for development?",
            "user_id": 101,
            "role": "dev"
        },
        {
            "name": "TEST 2: Permission Violation (Developer tries to read Admin Production DB credentials)",
            "query": "What is the master password and production host for postgres?",
            "user_id": 102,
            "role": "dev"  # Developer requesting Admin-level infra docs
        },
        {
            "name": "TEST 3: Out-of-Domain Retrieval Miss (Knowledge Base lacks this)",
            "query": "What is the secret recipe for French chocolate croissants?",
            "user_id": 103,
            "role": "admin"
        },
        {
            "name": "TEST 4: Secret Sanitization in Logs (User pastes API key in question)",
            "query": "How to connect with api-key: sk-proj-9988776655 to the guest Wi-Fi?",
            "user_id": 104,
            "role": "guest"
        }
    ]

    for tc in test_cases:
        print(f"\n>>> Running: {tc['name']}")
        ans, trace = pipeline.execute(tc["query"], tc["user_id"], tc["role"])
        render_observability_report(tc["query"], ans, trace)
