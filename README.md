# Lab 3: Chatbot vs ReAct Agent

This project compares a simple LLM chatbot with a ReAct-style HR agent. The agent can call HR tools to answer questions about employee profiles, leave balances, payroll, departments, and company HR policies.

## Features

- Chatbot baseline without tools.
- ReAct Agent v1 with `Thought -> Action -> Observation` loop.
- ReAct Agent v2 with parser retry, tool validation, required-argument validation, max-step guardrail, and HR-only scope.
- HR tools backed by mock data in `src/tools/hr_data.py`.
- Telemetry logs for latency, token usage, estimated cost, tool calls, and tool results.
- Streamlit GUI for live demo.
- Provider switching through `src/core/provider_factory.py`.

## Setup

### 1. Create environment file

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

### 2. Install dependencies

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Or, if you are not using the existing virtual environment:

```powershell
pip install -r requirements.txt
```

## Run with Ollama

The current local demo uses Ollama with `llama3.2`.

### 1. Install and start Ollama

Make sure Ollama is running, then pull the model:

```powershell
ollama pull llama3.2
```

Check available models:

```powershell
ollama list
```

### 2. Configure `.env`

```env
DEFAULT_PROVIDER=ollama
DEFAULT_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### 3. Run the Streamlit app

```powershell
.\.venv\Scripts\python.exe -m streamlit run src\Gui\app.py
```

Open:

```text
http://localhost:8501
```

## Run Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## Run Comparative Evaluation

This runs the chatbot baseline, ReAct Agent v1, and ReAct Agent v2 across 10 HR scenarios:

```powershell
.\.venv\Scripts\python.exe tests\test_hr_agent.py
```

The generated report is saved to:

```text
report/comparative_evaluation_report.md
```

## Optional Providers

The project also supports:

- OpenAI
- Gemini
- Local GGUF through `llama-cpp-python`

Set the provider in `.env`:

```env
DEFAULT_PROVIDER=openai
DEFAULT_MODEL=gpt-4o
```

or:

```env
DEFAULT_PROVIDER=gemini
DEFAULT_MODEL=gemini-2.5-flash
```

or:

```env
DEFAULT_PROVIDER=local
LOCAL_MODEL_PATH=./models/Phi-3-mini-4k-instruct-q4.gguf
```

For GGUF local mode, install `llama-cpp-python` separately because the current Ollama workflow does not require it.

## Project Structure

```text
src/
  agent/
    chatbot.py
    agent.py
  core/
    provider_factory.py
    openai_provider.py
    gemini_provider.py
    ollama_provider.py
    local_provider.py
  tools/
    hr_data.py
    hr_tools.py
  telemetry/
    logger.py
    metrics.py
  Gui/
    app.py
tests/
  test_hr_agent.py
  test_local.py
report/
  group_report/
  individual_reports/
```

## Notes

- Local Ollama inference is slower than cloud APIs, especially for ReAct because each step calls the model again.
- Logs are written to `logs/`.
- The HR agent is intentionally limited to HR-management questions only.
