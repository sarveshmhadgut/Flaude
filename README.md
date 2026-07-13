# Flaude – LangGraph based Agentic Chatbot

Flaude is a personal AI chatbot built on Google Gemini and LangGraph. It has persistent memory, a handful of useful tools, and a clean Streamlit interface. Nothing groundbreaking — just a well-built chat app that's fun to use and extend.

## What makes it interesting

Under the hood it's a proper LangGraph agent, so it does a bit more than a plain prompt-reply loop:

1. **Memory**: Remembers facts about you across sessions using a semantic memory store. Not just conversation history — actual notes it keeps.
2. **Tools**: Web search, live currency rates, math solving, file search. It picks the right one and asks before using it.
3. **RAG**: Drop in a PDF or text file and ask questions about it.
4. **Human-in-the-Loop**: Confirms tool calls before running them, so nothing happens without your say.

## Features

- **Agentic Workflow**: A LangGraph stateful agent that reasons, routes, and acts — not just generates.
- **Human-in-the-Loop**: Interrupts before every tool call so you can approve or cancel it.
- **Persistent Memory**: Cross-session checkpointing via PostgreSQL, plus a long-term semantic memory store.
- **RAG**: Upload PDFs or text files and query them using Chroma + Google Generative AI Embeddings.
- **Tool Use**: Web search, currency conversion, math solving (SymPy), and local file search.
- **Conversation Summarisation**: Automatically compresses old messages to stay within token limits — without losing context.
- **Auto Titles**: Generates a short, meaningful conversation title after your first message.
- **Multi-Session Sidebar**: Create, switch, and revisit conversations like a proper chat app.

## Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Backend** | Python 3.11+, LangGraph | The agent orchestration engine |
| **LLM** | Google Gemini (`langchain-google-genai`) | Reasoning, generation, and tool selection |
| **Memory** | PostgreSQL, SQLite | Persistent session checkpointing |
| **Vector Store** | Chroma (`langchain-chroma`) | Semantic document retrieval |
| **Embeddings** | Google Generative AI Embeddings | Turning text into meaning |
| **Document Loaders** | PyPDF, LangChain | Ingesting PDFs and text files |
| **Tools** | DuckDuckGo, SymPy, Requests | Web, math, and currency |
| **UI** | Streamlit | A clean, reactive chat interface |
| **Observability** | LangSmith | Tracing agent runs end-to-end |
| **Ops** | uv, Ruff, MyPy | Fast packaging, linting, type safety |

## How It Works

Imagine you type: *"What is the current USD to JPY exchange rate?"*

1. **Chat Node**: Gemini reads your message and decides this is a factual lookup — it shouldn't guess. It selects the `get_conversion_rate` tool.
2. **Human-in-the-Loop**: Flaude pauses and asks: *"I'd like to call get_conversion_rate. Allow?"* You say yes.
3. **Tool Node**: The tool fires, hits the Exchange Rate API, and returns live data.
4. **Chat Node (again)**: Gemini reads the result and writes a clean, natural response.
5. **Memory Node**: Flaude checks if there's anything worth keeping — like *"User tracks currency rates"* — and stores it for next time.
6. **Summary Node** *(if needed)*: If the conversation is running long, older messages get compressed into a summary so nothing important gets dropped.

## Directory Structure

```text
Flaude/
├── .github/
│   └── workflows/
│       ├── ci.yml          # Ruff format, lint, and MyPy on every push
│       └── codeql.yml      # Weekly CodeQL security scan
├── configs/                # YAML config files (model params, paths, etc.)
├── src/
│   ├── core/
│   │   ├── agents/         # LLM chain definitions (chat, memory, summary)
│   │   ├── capabilities/   # Memory, RAG, and title generation logic
│   │   ├── tools/          # Web search, math, RAG tool, file search
│   │   └── workflow/       # LangGraph graph, node functions, state schema
│   ├── exception/          # Custom exception with file + line tracing
│   ├── infra/              # DB connections, LLM init, CSS loader
│   ├── logger/             # Rotating file + coloured console logger
│   └── ui/
│       ├── components/     # Streamlit chat and sidebar components
│       └── state.py        # Session state initialisation
├── main.py                 # Entry point
├── pyproject.toml
└── uv.lock
```

## Getting Started

### 1. Setup

Clone the repo and install everything with `uv`:

```bash
git clone <your-repo-url>
cd Flaude
uv sync
```

### 2. Configure

You'll need a Google API key and, optionally, keys for currency conversion and LangSmith tracing. Create a `.env` in the project root:

```env
GOOGLE_API_KEY="your_google_api_key"
EXCHANGE_RATE_KEY="your_exchangerate_api_key"   # optional, for currency tool
LANGSMITH_API_KEY="your_langsmith_api_key"      # optional, for tracing
```

Flaude uses **PostgreSQL** for persistent session checkpointing. Point it to a running Postgres instance via the connection string in `configs/`. If you just want to try it locally, the SQLite backend requires zero setup and works out of the box.

### 3. Run

```bash
uv run streamlit run main.py
```

Open **http://localhost:8501** and start chatting.
