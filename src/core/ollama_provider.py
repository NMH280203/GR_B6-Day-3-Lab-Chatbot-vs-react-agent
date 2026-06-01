import time
import os
import requests
from typing import Dict, Any, Optional, Generator
from src.core.llm_provider import LLMProvider


class OllamaProvider(LLMProvider):
    """
    LLM Provider for local models served via Ollama.
    Uses Ollama's OpenAI-compatible REST API (no API key required).
    """

    def __init__(self, model_name: str = "llama3.2", base_url: str = "http://localhost:11434"):
        super().__init__(model_name=model_name, api_key=None)
        self.provider = "ollama"
        self.base_url = base_url.rstrip("/")
        self._check_connection()

    def _check_connection(self):
        """Verify Ollama server is running and model is available."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            models = [m["name"] for m in resp.json().get("models", [])]
            # Accept if model name prefix matches (e.g. "llama3.2" matches "llama3.2:latest")
            found = any(m.startswith(self.model_name.split(":")[0]) for m in models)
            if not found:
                available = ", ".join(models) if models else "(none)"
                raise RuntimeError(
                    f"Model '{self.model_name}' not found in Ollama.\n"
                    f"Available models: {available}\n"
                    f"Run: ollama pull {self.model_name}"
                )
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Cannot connect to Ollama at http://localhost:11434.\n"
                "Please make sure Ollama is running: start Ollama app or run 'ollama serve'."
            )

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": self.max_tokens,
            }
        }

        response = requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        data = response.json()

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        content = data["message"]["content"]

        # Ollama returns token counts in eval_count / prompt_eval_count
        prompt_tokens = data.get("prompt_eval_count", 0)
        completion_tokens = data.get("eval_count", 0)
        total_tokens = prompt_tokens + completion_tokens

        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
        }

        from src.telemetry.metrics import tracker
        tracker.track_request(
            provider="ollama",
            model=self.model_name,
            usage=usage,
            latency_ms=latency_ms
        )

        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "ollama"
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": True,
            "options": {
                "num_predict": self.max_tokens,
            }
        }

        with requests.post(
            f"{self.base_url}/api/chat",
            json=payload,
            stream=True,
            timeout=120
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    import json
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if chunk.get("done"):
                        break
