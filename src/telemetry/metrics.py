import time
from typing import Dict, Any, List
from src.telemetry.logger import logger

class PerformanceTracker:
    """
    Tracking industry-standard metrics for LLMs.
    """
    def __init__(self):
        self.session_metrics = []

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        """
        Logs a single request metric to our telemetry.
        """
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_estimate": self._calculate_cost(model, usage) # Mock cost calculation
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """
        Calculates the real estimated API cost for OpenAI GPT-4o and Google Gemini 2.5 Flash.
        """
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        
        model_lower = model.lower()
        if "gpt-4" in model_lower or "openai" in model_lower:
            # GPT-4o: $2.50/M input, $10.00/M output
            return (prompt_tokens * 2.50 + completion_tokens * 10.00) / 1_000_000
        elif "gemini-2.5" in model_lower or "google" in model_lower:
            # Gemini 2.5 Flash: $0.075/M input, $0.30/M output
            return (prompt_tokens * 0.075 + completion_tokens * 0.30) / 1_000_000
        elif "gemini-1.5" in model_lower:
            # Gemini 1.5 Flash: $0.075/M input, $0.30/M output (similar)
            return (prompt_tokens * 0.075 + completion_tokens * 0.30) / 1_000_000
        else:
            # Local models are free
            return 0.0

# Global tracker instance
tracker = PerformanceTracker()