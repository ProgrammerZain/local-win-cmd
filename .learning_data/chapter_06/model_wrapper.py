from abc import ABC, abstractmethod
import time
import ollama

class BaseLLM(ABC):
    """Abstract interface for local language models."""
    
    @abstractmethod
    def generate(self, prompt: str) -> str:
        pass

class OllamaLLM(BaseLLM):
    """Concrete wrapper for local Ollama service."""
    
    def __init__(self, model_name: str = "qwen2.5:1.5b"):
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        response = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]

class MockLLM(BaseLLM):
    """Deterministic mock LLM for fast unit testing and CI/CD without CPU/GPU overhead."""
    
    def __init__(self, canned_response: str = "TICKET-RESOLVED: Restart the service and verify network settings."):
        self.canned_response = canned_response
        self.call_count = 0

    def generate(self, prompt: str) -> str:
        self.call_count += 1
        return self.canned_response

class FallbackLLM(BaseLLM):
    """Resilience wrapper: attempts primary LLM, gracefully falls back if it fails."""

    def __init__(self, primary: BaseLLM, backup: BaseLLM):
        self.primary = primary
        self.backup = backup

    def generate(self, prompt: str) -> str:
        try:
            return self.primary.generate(prompt)
        except Exception as e:
            print(f"  [WARN] Primary model failed ({e}). Switching to fallback provider...")
            return self.backup.generate(prompt)

# =====================================================================
# REAL-WORLD APPLICATION LAYER (Depends ONLY on BaseLLM, NOT on Ollama!)
# =====================================================================

class ITSupportBot:
    """
    Business application service.
    Notice: It has ZERO import of 'ollama' or specific vendor SDKs.
    Any provider implementing BaseLLM can be injected (Dependency Injection).
    """

    def __init__(self, llm: BaseLLM):
        self.llm = llm

    def triage_ticket(self, user: str, issue: str) -> str:
        prompt = (
            f"You are an IT Support assistant. Provide a 1-sentence action plan for this issue.\n"
            f"User: {user}\n"
            f"Issue: {issue}\n"
            f"Action Plan:"
        )
        return self.llm.generate(prompt)


def get_llm_provider(mode: str) -> BaseLLM:
    """Factory Pattern: Choose provider based on config, CLI flag, or environment."""
    if mode == "production":
        return OllamaLLM("qwen2.5:1.5b")
    elif mode == "test":
        return MockLLM()
    elif mode == "resilient":
        return FallbackLLM(
            primary=OllamaLLM("non-existent-broken-model"),
            backup=MockLLM("Service is operating in safe offline mode. Ticket logged.")
        )
    raise ValueError(f"Unknown mode: {mode}")


if __name__ == "__main__":
    ticket_user = "Zain"
    ticket_issue = "Cannot connect to local PostgreSQL port 5432"

    print("\n" + "=" * 60)
    print("  REAL-WORLD USE CASES FOR BaseLLM ABSTRACTION")
    print("=" * 60)

    # -------------------------------------------------------------
    # Use Case 1: Fast CI/CD Unit Testing (No Ollama, No CPU load)
    # -------------------------------------------------------------
    print("\n[USE CASE 1: Automated Unit Testing]")
    mock_engine = MockLLM()
    test_app = ITSupportBot(llm=mock_engine)

    t0 = time.perf_counter()
    test_result = test_app.triage_ticket(ticket_user, ticket_issue)
    t1 = time.perf_counter()

    print(f"  Output : {test_result}")
    print(f"  Speed  : {(t1 - t0) * 1000:.3f} ms (Runs in CI pipelines without Ollama installed!)")
    print(f"  Assert : Mock was called {mock_engine.call_count} time(s) -> TEST PASSED")

    # -------------------------------------------------------------
    # Use Case 2: Production Execution (Real Local LLM)
    # -------------------------------------------------------------
    print("\n[USE CASE 2: Production Environment (Real Local LLM)]")
    try:
        prod_engine = OllamaLLM("qwen2.5:1.5b")
        prod_app = ITSupportBot(llm=prod_engine)

        t0 = time.perf_counter()
        prod_result = prod_app.triage_ticket(ticket_user, ticket_issue)
        t1 = time.perf_counter()

        print(f"  Output : {prod_result.strip()}")
        print(f"  Speed  : {t1 - t0:.2f} s")
    except Exception as exc:
        print(f"  [ERROR] Ollama connection failed: {exc}")

    # -------------------------------------------------------------
    # Use Case 3: Automatic Fault-Tolerance & Fallback
    # -------------------------------------------------------------
    print("\n[USE CASE 3: Automatic Fault-Tolerance & Fallback]")
    resilient_engine = get_llm_provider("resilient")
    resilient_app = ITSupportBot(llm=resilient_engine)

    safe_result = resilient_app.triage_ticket(ticket_user, ticket_issue)
    print(f"  Output : {safe_result.strip()}")

    print("\n" + "=" * 60)
    print("Takeaway: ITSupportBot never changed its code across all 3 scenarios!")
    print("=" * 60 + "\n")
