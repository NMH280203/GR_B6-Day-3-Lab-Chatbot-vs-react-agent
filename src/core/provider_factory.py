import os
from dotenv import load_dotenv
from src.core.llm_provider import LLMProvider
from src.core.openai_provider import OpenAIProvider
from src.core.gemini_provider import GeminiProvider

def get_provider() -> LLMProvider:
    """
    Factory function to initialize and return the LLMProvider configured in .env.
    Supported providers: openai | google | gemini | ollama | local
    """
    load_dotenv()

    provider_type = os.getenv("DEFAULT_PROVIDER", "google").lower()
    model_name = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")

    if provider_type == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or "your_" in api_key:
            api_key = None
        return OpenAIProvider(model_name=model_name, api_key=api_key)

    elif provider_type in ["google", "gemini"]:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or "your_" in api_key:
            api_key = None
        return GeminiProvider(model_name=model_name, api_key=api_key)

    elif provider_type == "ollama":
        from src.core.ollama_provider import OllamaProvider
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", model_name)
        return OllamaProvider(model_name=ollama_model, base_url=base_url)

    elif provider_type == "local":
        from src.core.local_provider import LocalProvider
        model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
        return LocalProvider(model_path=model_path)

    else:
        raise ValueError(f"Unknown DEFAULT_PROVIDER: {provider_type}. Valid options: openai | google | gemini | ollama | local")
