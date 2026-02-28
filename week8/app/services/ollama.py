"""Ollama service for AI summarization."""

import httpx
import os
from typing import Optional

class OllamaService:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.model = os.environ.get("OLLAMA_MODEL", "gemma3:1b")
        self.timeout_seconds = self._load_timeout_seconds()

    def _load_timeout_seconds(self) -> float:
        """Load Ollama request timeout from env with safe fallback (default 300s)."""
        raw = os.environ.get("OLLAMA_TIMEOUT_SECONDS", "300")
        try:
            timeout = float(raw)
            if timeout <= 0:
                raise ValueError
            return timeout
        except ValueError:
            return 300.0

    def _get_client(self, timeout: Optional[float] = None) -> httpx.Client:
        """Get httpx client without proxy for localhost."""
        t = timeout if timeout is not None else self.timeout_seconds
        return httpx.Client(timeout=httpx.Timeout(t), trust_env=False)

    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            client = self._get_client(timeout=5)
            response = client.get(f"{self.base_url}/api/tags")
            client.close()
            return response.status_code == 200
        except:
            return False

    def generate_summary(self, paper_title: str, paper_abstract: str) -> Optional[str]:
        """Generate AI summary for a paper."""
        if not self.is_available():
            return None

        prompt = f"""You are a research paper assistant. Please provide a brief summary (2-3 sentences) of this paper.

Title: {paper_title}

Abstract: {paper_abstract}

Summary:"""

        try:
            client = self._get_client()
            response = client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            client.close()
            if response.status_code == 200:
                return response.json().get("response", "").strip()
        except Exception as e:
            print(f"Error generating summary: {e}")
        return None

    def chat(self, message: str, context: Optional[str] = None) -> Optional[str]:
        """Send a message to Ollama, optionally with context (e.g. paper full text)."""
        if not self.is_available():
            return None
        prompt = message
        if context:
            prompt = f"""Use the following context to answer the user's question. If the context is empty or irrelevant, answer generally.

Context:
{context[:12000]}

User question: {message}

Answer:"""
        try:
            client = self._get_client()
            response = client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            client.close()
            if response.status_code == 200:
                return response.json().get("response", "").strip()
        except Exception as e:
            print(f"Error in chat: {e}")
        return None
