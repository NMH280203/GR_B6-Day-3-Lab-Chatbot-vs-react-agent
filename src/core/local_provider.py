import os
import time
from typing import Dict, Any, Optional, Generator

from src.core.llm_provider import LLMProvider


class LocalProvider(LLMProvider):
    """
    Local GGUF provider using llama-cpp-python.
    Optimized for CPU inference.
    """
    def __init__(
        self,
        model_path: str,
        n_ctx: int = 4096,
        n_threads: Optional[int] = None
    ):
        """
        Initialize the local Llama model.

        Args:
            model_path: Path to the .gguf model file.
            n_ctx: Context window size.
            n_threads: Number of CPU threads to use. Defaults to all available.
        """
        super().__init__(model_name=os.path.basename(model_path))

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at {model_path}. Please download it first."
            )

        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise ImportError(
                "llama-cpp-python is required for DEFAULT_PROVIDER=local. "
                "Install it with: pip install llama-cpp-python"
            ) from exc

        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads or os.cpu_count(),
            n_batch=512,
            verbose=False
        )

    def _build_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Phi-3 Instruct prompt template
        """

        if system_prompt:
            return (
                f"<|system|>\n"
                f"{system_prompt}<|end|>\n"
                f"<|user|>\n"
                f"{prompt}<|end|>\n"
                f"<|assistant|>"
            )

        return (
            f"<|user|>\n"
            f"{prompt}<|end|>\n"
            f"<|assistant|>"
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:

        start_time = time.time()

        full_prompt = self._build_prompt(
            prompt=prompt,
            system_prompt=system_prompt
        )

        response = self.llm(
            full_prompt,
            max_tokens=self.max_tokens,
            temperature=0.7,
            top_p=0.9,
            stop=[
                "<|end|>",
                "Observation:"
            ],
            echo=False
        )

        latency_ms = int(
            (time.time() - start_time) * 1000
        )

        content = (
            response["choices"][0]["text"]
            .strip()
        )

        usage = response.get(
            "usage",
            {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        )

        from src.telemetry.metrics import tracker
        tracker.track_request(
            provider="local",
            model=self.model_name,
            usage=usage,
            latency_ms=latency_ms
        )

        return {
            "content": content,
            "usage": usage,
            "latency_ms": latency_ms,
            "provider": "local"
        }

    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> Generator[str, None, None]:

        full_prompt = self._build_prompt(
            prompt=prompt,
            system_prompt=system_prompt
        )

        stream = self.llm(
            full_prompt,
            max_tokens=self.max_tokens,
            temperature=0.7,
            top_p=0.9,
            stop=[
                "<|end|>",
                "Observation:"
            ],
            stream=True
        )

        for chunk in stream:
            token = chunk["choices"][0]["text"]

            if token:
                yield token
