# HR Agentic Workspace

This repository contains a Streamlit-based HR assistant prototype that supports local Ollama models, local GGUF models via `llama-cpp-python`, and cloud providers through a unified LLM provider interface.

## Project Overview

- `src/gui/app.py` — Streamlit front-end with chat UI, provider status, and performance metrics.
- `src/agent/agent.py` — ReAct agent implementation for multi-step reasoning.
- `src/agent/chatbot.py` — Baseline chatbot flow.
- `src/core/provider_factory.py` — Provider selection from `.env`.
- `src/core/ollama_provider.py` — Ollama REST API integration.
- `src/core/local_provider.py` — Local GGUF model support with `llama-cpp-python`.
- `src/tools/hr_tools.py` — HR tool metadata for agent actions.
- `src/telemetry/metrics.py` — Logging and request metrics.

## Requirements

From the `test` folder, install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the `test` folder and configure the provider.

### Ollama setup

```env
DEFAULT_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

If your Ollama model is tagged, use the exact name returned by `ollama ls`, for example:

```env
OLLAMA_MODEL=llama3.2:latest
```

### Local GGUF model setup

```env
DEFAULT_PROVIDER=local
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

### Cloud provider setup

OpenAI:

```env
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
OPENAI_API_KEY=your_api_key
```

Gemini:

```env
DEFAULT_PROVIDER=google
DEFAULT_MODEL=gemini-2.5-flash
GEMINI_API_KEY=your_api_key
```

## Run the app

From the `test` folder:

```powershell
python -m streamlit run src/gui/app.py
```

Then open the local URL printed in the Streamlit terminal.

## Ollama Troubleshooting

If the app shows an Ollama warning:

- Confirm `.env` contains `DEFAULT_PROVIDER=ollama`
- Confirm `OLLAMA_BASE_URL` is correct
- Run `ollama serve` or start the Ollama app
- Run `ollama ls` to verify the model is pulled
- Use the exact `OLLAMA_MODEL` name from `ollama ls`

## Notes on providers

Supported provider values in `.env`:

- `ollama` — local Ollama server
- `local` — local GGUF model via `llama-cpp-python`
- `google` / `gemini` — Gemini API
- `openai` — OpenAI API

The provider factory in `src/core/provider_factory.py` loads the selected provider and model at startup.

## Usage

- Select the agent mode in the sidebar: `Chatbot Baseline`, `ReAct Agent v1 (Basic)`, or `ReAct Agent v2 (Production)`.
- Adjust `Max Output Tokens` and `Max ReAct Steps` as needed.
- Ask HR questions about employees, payroll, leave, and policies.

## Recommended workflow

1. Configure `.env`
2. Start your LLM provider (`ollama serve`, local model, or cloud API)
3. Launch Streamlit
4. Use the chat UI to query HR data
5. Review sidebar connection status and metrics

## License

This repository is for educational/demo use.
