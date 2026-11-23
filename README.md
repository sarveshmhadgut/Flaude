# Flaude – LangGraph based Agentic Chatbot

Flaude turns the typical LLM chat experience into a capable, personal assistant. Instead of relying on a plain prompt-reply loop, it uses LangGraph to orchestrate a smart agentic workflow—combining persistent memory, dynamic tool execution, and human-in-the-loop safeguards—to give you a chatbot that actually reasons, researches, and remembers.

---

## Table of Contents

- [What makes it interesting](#what-makes-it-interesting)
- [The Problem: Why Agentic Architecture Matters](#the-problem-why-agentic-architecture-matters)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture Deep Dive](#architecture-deep-dive)
  - [High-Level System Architecture](#high-level-system-architecture)
  - [LangGraph Workflow and Subgraphs (The Core State Machine)](#langgraph-workflow-and-subgraphs-the-core-state-machine)
  - [State Schema and Delta Propagation](#state-schema-and-delta-propagation)
  - [Core Subsystems Deep Dive](#core-subsystems-deep-dive)
- [How It Works](#how-it-works)
- [Directory Structure](#directory-structure)
- [Getting Started](#getting-started)
  - [1. Setup](#1-setup)
  - [2. Configure](#2-configure)
  - [3. Run](#3-run)

---

## What makes it interesting

Under the hood it's a proper LangGraph agent, so it does a bit more than a plain prompt-reply loop:

- **Memory**: Remembers facts about you across sessions using a semantic memory store. Not just conversation history — actual notes it keeps.
- **Tools**: Web search, live currency rates, math solving, file search. It picks the right one and asks before using it.
- **RAG**: Drop in a PDF or text file and ask questions about it.
- **Human-in-the-Loop**: Confirms tool calls before running them, so nothing happens without your say.

---

## The Problem: Why Agentic Architecture Matters

Standard LLM wrappers fail in 5 major production areas:

| Production Failure Mode | Standard LLM Wrapper | Flaude Cognitive Architecture |
| :--- | :--- | :--- |
| **Stateless Amnesia** | Loses context across sessions; requires repeating facts | **Dual-Layer Memory**: PostgresSaver (thread checkpoints) + PostgresStore (768-dim semantic vectors) |
| **Autonomous Agent Liability** | Blind tool execution risking accidental cost/actions | **Human-in-the-Loop (HITL)**: Native `interrupt()` gate requiring human approval |
| **Context Window Explosion** | Crashes or naively truncates oldest messages | **Context Compactor**: Automated 8,000 token threshold with `RemoveMessage` state pruning |
| **Hallucinated Tasks** | Hallucinates multi-digit arithmetic or outdated forex | **Specialized Tool Ecosystem**: SymPy exact math, ExchangeRate API, live DuckDuckGo |
| **Unscoped Document RAG** | Single shared vector DB causing context bleeding | **Thread-Isolated RAG**: Language-aware syntax splitting + per-thread Chroma collections |

---

## Features

- **Agentic Workflow**: A LangGraph stateful agent that reasons, routes, and acts — not just generates.
- **Human-in-the-Loop**: Interrupts before every tool call so you can approve or cancel it.
- **Persistent Memory**: Cross-session checkpointing via PostgreSQL, plus a long-term semantic memory store.
- **RAG**: Upload PDFs or text files and query them using Chroma + Google Generative AI Embeddings.
- **Tool Use**: Web search, currency conversion, math solving (SymPy), and local file search.
- **Conversation Summarisation**: Automatically compresses old messages to stay within token limits — without losing context.
- **Auto Titles**: Generates a short, meaningful conversation title after your first message.
- **Multi-Session Sidebar**: Create, switch, and revisit conversations like a proper chat app.

---

## Tech Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Backend** | Python 3.14+, LangGraph | The agent orchestration engine |
| **LLM** | Google Gemini (`langchain-google-genai`) | Reasoning, generation, and tool selection |
| **Memory** | PostgreSQL, SQLite | Persistent session checkpointing |
| **Vector Store** | Chroma (`langchain-chroma`) | Semantic document retrieval |
| **Embeddings** | Google Generative AI Embeddings | Turning text into meaning |
| **Document Loaders** | PyPDF, LangChain | Ingesting PDFs and text files |
| **Tools** | DuckDuckGo, SymPy, Requests | Web, math, and currency |
| **UI** | Streamlit | A clean, reactive chat interface |
| **Observability** | LangSmith | Tracing agent runs end-to-end |

---

## Architecture Deep Dive

### High-Level System Architecture

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "edgeLabelBackground": "transparent",
    "lineColor": "#C7C6F5"
  }
}}%%
graph TB
    subgraph UI ["Client Layer (Streamlit UI & Custom CSS)"]
        A["User Input / File Upload<br/>(src/ui/app.py)"]
        B["Sidebar & Session Manager<br/>(src/ui/components/sidebar.py)"]
        C["Live Token Streamer<br/>(src/ui/components/chat.py)"]
        D["HITL Approval Modal<br/>(Approve / Reject Buttons)"]
    end

    subgraph Orchestrator ["LangGraph Orchestration Engine (src/core/workflow/)"]
        E["Compiled State Graph<br/>(graph.py)"]
        F["Memory Node<br/>(Semantic Search & Extraction)"]
        G["Chat Agent Node<br/>(Gemini 4 Hydrogen + Tools)"]
        H["Tools Subgraph<br/>(approve_tools -> use_tools)"]
        I["Summary Subgraph<br/>(route_summary -> summarize)"]
    end

    subgraph Tools ["Tool Ecosystem (src/core/tools/)"]
        T1["DuckDuckGo<br/>(web_search)"]
        T2["ExchangeRate API<br/>(get_conversion_rate)"]
        T3["SymPy Engine<br/>(math_eval)"]
        T4["Filesystem Search<br/>(file_search)"]
        T5["Chroma Retriever<br/>(rag)"]
    end

    subgraph Storage ["Persistence & Infrastructure (src/infra/)"]
        DB1[("PostgreSQL Saver<br/>Thread Checkpoints")]
        DB2[("PostgreSQL Store<br/>768-dim Semantic Vectors")]
        DB3[("SQLite DB<br/>Thread Title Mappings")]
        DB4[("Chroma Vector DB<br/>Thread-Isolated Collections")]
    end

    subgraph Observability ["Telemetry & Tracking"]
        LS["LangSmith Platform<br/>(RunTree & @traceable)"]
        LOG["Colorlog Console +<br/>Rotating File Handler"]
    end

    A --> E
    E --> F
    F <--> DB2
    F --> G
    G -->|"tool_calls emitted"| H
    H -->|"interrupt()"| D
    D -->|"Command(resume=True)"| H
    H --> Tools
    Tools --> H
    H --> G
    G -->|"No tools / Final reply"| I
    I -->|"Tokens > 8,000"| I
    I -->|"Command(update=PARENT)"| E
    E --> C
    E <--> DB1
    B <--> DB3
    T5 <--> DB4
    E -.-> LS
    E -.-> LOG

    style UI fill:#000,stroke:#7CD6FF,stroke-dasharray: 4 4,color:#7CD6FF
    style Orchestrator fill:#000,stroke:#B5A3FF,color:#B5A3FF
    style Tools fill:#000,stroke:#FDE6B0,color:#FDE6B0
    style Storage fill:#000,stroke:#80FFEA,color:#80FFEA
    style Observability fill:#000,stroke:#FFA2B8,color:#FFA2B8

    classDef clientNode fill:#7CD6FF22,stroke:#7CD6FF,color:#F0F0FF;
    classDef orchNode fill:#B5A3FF22,stroke:#B5A3FF,color:#FFFFFF;
    classDef toolNode fill:#FDE6B022,stroke:#FDE6B0,color:#FFFFFF;
    classDef storageNode fill:#80FFEA22,stroke:#80FFEA,color:#F0F0FF;
    classDef teleNode fill:#FEB2D922,stroke:#FEB2D9,color:#FFFFFF;

    class A,B,C,D clientNode;
    class E,F,G,H,I orchNode;
    class T1,T2,T3,T4,T5 toolNode;
    class DB1,DB2,DB3,DB4 storageNode;
    class LS,LOG teleNode;

    linkStyle default stroke:#aaaaaa,stroke-width:1px;
```

---

### LangGraph Workflow and Subgraphs (The Core State Machine)

The application compiles two specialized subgraphs into a master state machine in [`src/core/workflow/graph.py`](https://github.com/sarveshmhadgut/Flaude/blob/main/src/core/workflow/graph.py):

```mermaid
%%{init: {
  "theme": "base",
  "themeVariables": {
    "edgeLabelBackground": "transparent",
    "lineColor": "#aaaaaa"
  }
}}%%
flowchart TD
    __start__([<p>__start__</p>]):::first

    subgraph MemorySub ["memory (Dual-Layer Semantic Memory)"]
        M1["FetchMemories"]
        M2["ExtractFacts"]
        M3["PersistMemories"]

        M1 -->|"MEMORY_CHAIN(DecisionSchema)"| M2
        M2 -->|"store.put() if update_memory=True"| M3
    end

    __start__ -->|"store.search(namespace, query=msg)"| M1
    M3 -->|"Inject Context (Summary + Memories + Active File)"| CHAT_NODE

    subgraph ChatSub ["chat (Gemini 4 Hydrogen Agent)"]
        CHAT_NODE["CallGemini<br/><i>CHAT_CHAIN.invoke()</i>"]
    end

    CHAT_NODE --> TC{tools_condition}

    subgraph ToolsSub ["tools_workflow (Human-in-the-Loop Gate)"]
        APPROVE["approve_tools<br/><i>Inspect AIMessage.tool_calls</i>"]
        HALT["Halt<br/><i>interrupt(required_tools)</i>"]
        USER_DECISION{User Decision<br/>UI Wait}
        USE_TOOLS["use_tools<br/><i>Return ToolMessage</i>"]
        ABORT_TOOLS["AbortTools<br/><i>Tool Execution Rejected</i>"]

        APPROVE --> HALT
        HALT --> USER_DECISION
        USER_DECISION -->|"Command(resume=True)"| USE_TOOLS
        USER_DECISION -->|"Command(resume=False)"| ABORT_TOOLS
    end

    TC -->|"tools"| APPROVE
    USE_TOOLS -->|"Loop back for Synthesis"| CHAT_NODE
    ABORT_TOOLS --> __end__

    subgraph SummarySub ["summary_workflow (Context Compaction)"]
        ROUTE_SUMM{route_summary}
        SUMMARIZE["summarize<br/><i>SUMMARY_CHAIN + RemoveMessage</i>"]

        ROUTE_SUMM -->|"Tokens > 8,000"| SUMMARIZE
    end

    TC -->|"__end__"| ROUTE_SUMM
    ROUTE_SUMM -->|"Tokens <= 8,000"| __end__
    SUMMARIZE -->|"Command(update=PARENT)"| __end__

    __end__([<p>__end__</p>]):::last

    style MemorySub fill:#000,stroke:#B5A3FF,color:#C7C6F5
    style ChatSub fill:#000,stroke:#B5A3FF,color:#C7C6F5
    style ToolsSub fill:#000,stroke:#B5A3FF,color:#C7C6F5
    style SummarySub fill:#000,stroke:#B5A3FF,color:#C7C6F5

    classDef default fill:#B5A3FF,color:#1e1e2e;
    classDef first fill:#AF87FF,color:#1e1e2e;
    classDef last fill:#AF87FF,color:#1e1e2e;
    classDef decisionNode fill:#FCCEA1,color:#1e1e2e;
    classDef actionNode fill:#B5A3FF,color:#1e1e2e;

    class TC,USER_DECISION,ROUTE_SUMM decisionNode;
    class APPROVE,HALT,USE_TOOLS,ABORT_TOOLS actionNode;

    linkStyle default stroke:#aaaaaa,stroke-width:1px;
```

---

### State Schema and Delta Propagation

The state schema is defined in [`src/core/workflow/state.py`](https://github.com/sarveshmhadgut/Flaude/blob/main/src/core/workflow/state.py):

```python
class MessagesState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    messages_summary: NotRequired[str]
```

#### How the State Machine Handles Data Mutations

- **`add_messages` Reducer**: LangGraph's prebuilt reducer handles both appending new messages (`AIMessage`, `HumanMessage`, `ToolMessage`) and deleting existing messages when a `RemoveMessage(id=...)` object is emitted.
- **`messages_summary` Context Carrier**: An evolving string representing the compressed dialogue history prior to the active message window.
- **Cross-Subgraph State Sync (`Command.PARENT`)**: In [`src/core/workflow/nodes.py`](https://github.com/sarveshmhadgut/Flaude/blob/main/src/core/workflow/nodes.py), the `summarize` node runs inside the `summary_subgraph`. To update the parent graph's state and prune messages globally, it issues:

```python
return Command(
    update={
        "messages_summary": updated_summary,
        "messages": [
            RemoveMessage(id=str(message.id))
            for message in state["messages"][:-4]
        ],
    },
    graph=Command.PARENT,
)
```

---

### Core Subsystems Deep Dive

#### 1. Dual-Layer Semantic Memory ([`src/core/capabilities/memory.py`](https://github.com/sarveshmhadgut/Flaude/blob/main/src/core/capabilities/memory.py))

Flaude separates short-term conversation state from persistent user facts:

- **Thread Checkpointing (`PostgresSaver`)**: Captures exact snapshots of the active graph state, allowing threads to survive server restarts and seamlessly resume interruptions.
- **Semantic Fact Store (`PostgresStore`)**: User memories are partitioned under namespace `("user_id", user_id)` and indexed with Google Generative AI embeddings (`models/gemini-embedding-2`, 768 dimensions).
- **Structured Extraction**: The memory node uses Pydantic structured output (`DecisionSchema`) to extract durable facts with snake_case keys (e.g. `profession`, `tech_stack`), ignoring transient small talk.

```python
class MemorySchema(BaseModel):
    key: str = Field(description="Unique snake_case identifier, e.g. 'profession'")
    value: str = Field(description="Complete factual statement optimized for semantic search")
    importance: float = Field(description="Float from 0.0 to 1.0 indicating criticality")

class DecisionSchema(BaseModel):
    update_memory: bool
    memories: list[MemorySchema]
```

#### 2. Human-in-the-Loop (HITL) Execution Gate ([`src/core/workflow/nodes.py`](https://github.com/sarveshmhadgut/Flaude/blob/main/src/core/workflow/nodes.py))

To prevent unmonitored execution of external tools:

- **`approve_tools`**: Inspects `AIMessage.tool_calls` and triggers LangGraph's native `interrupt({"required_tools": [...]})`.
- **`GraphInterrupt`**: Raises an interrupt exception, freezing graph state to PostgreSQL and unlocking Approve/Reject controls in the UI.
- **Resumption**:
  - User clicks **Approve**: Streamlit sends `Command(resume=True)` → routes to `use_tools`.
  - User clicks **Reject**: Streamlit sends `Command(resume=False)` → routes to `__end__` with `"Tool execution was rejected."`

#### 3. Context Window Compactor & State Pruning ([`src/core/workflow/nodes.py`](https://github.com/sarveshmhadgut/Flaude/blob/main/src/core/workflow/nodes.py))

Prevents context window exhaustion without losing core background:

- **Token Threshold Gate (`route_summary`)**: Evaluates token consumption via `count_tokens_approximately()`. If tokens $\le$ 8,000, it bypasses summarization (`__end__`).
- **Running Summary (`summarize`)**: When tokens > 8,000, `SUMMARY_CHAIN` condenses earlier messages into `messages_summary`.
- **Pruning**: Emits `RemoveMessage(id=...)` on oldest messages (`state["messages"][:-4]`) and updates `messages_summary` on the parent graph via `Command(update=..., graph=Command.PARENT)`.

#### 4. Thread-Isolated Language-Aware RAG ([`src/core/capabilities/rag.py`](https://github.com/sarveshmhadgut/Flaude/blob/main/src/core/capabilities/rag.py))

- **Syntax-Aware Code Ingestion**: Maps file extensions to LangChain Language enums (`.py`, `.md`, `.js`, `.ts`, `.java`, `.cpp`, `.html`), preserving class and function AST boundaries.
- **Thread Isolation**: Chroma collections are named after `current_thread`. Uploading a new file to the active thread clears and recreates the collection, ensuring zero cross-thread context contamination.

#### 5. Tool Ecosystem ([`src/core/tools/`](https://github.com/sarveshmhadgut/Flaude/blob/main/src/core/tools))

| Tool | Implementation | File | Purpose | Why Not Let LLM Guess? |
| :--- | :--- | :--- | :--- | :--- |
| **`math_eval`** | `sympy.sympify(expression)` | [`math.py`](https://github.com/sarveshmhadgut/Flaude/blob/main/src/core/tools/math.py) | High-precision arithmetic & algebra | Eliminates LLM math hallucinations; exact symbolic math engine. |
| **`web_search`** | `DuckDuckGoSearchRun()` | [`web.py`](https://github.com/sarveshmhadgut/Flaude/blob/main/src/core/tools/web.py) | Real-time web retrieval | Fetches live, post-training data without paid API quotas. |
| **`get_conversion_rate`** | ExchangeRate-API via `requests.get` | [`web.py`](https://github.com/sarveshmhadgut/Flaude/blob/main/src/core/tools/web.py) | Live foreign currency exchange | Forex rates fluctuate every minute; model weights cannot know current rates. |
| **`file_search`** | `Path.cwd().rglob(filename)` | [`files.py`](https://github.com/sarveshmhadgut/Flaude/blob/main/src/core/tools/files.py) | Local directory file search | Grants read-access to inspect local workspace files upon request. |
| **`rag`** | Chroma VectorStore retriever | [`rag.py`](https://github.com/sarveshmhadgut/Flaude/blob/main/src/core/tools/rag.py) | Thread-isolated document retrieval | Dense semantic search over uploaded PDFs and codebases. |

---

## How It Works

Imagine you type: *"What is the current USD to JPY exchange rate?"*

1. **Chat Node**: Gemini reads your message and decides this is a factual lookup — it shouldn't guess. It selects the `get_conversion_rate` tool.
2. **Human-in-the-Loop**: Flaude pauses and asks: *"I'd like to call get_conversion_rate. Allow?"* You say yes.
3. **Tool Node**: The tool fires, hits the Exchange Rate API, and returns live data.
4. **Chat Node (again)**: Gemini reads the result and writes a clean, natural response.
5. **Memory Node**: Flaude checks if there's anything worth keeping — like *"User tracks currency rates"* — and stores it for next time.
6. **Summary Node (if needed)**: If the conversation is running long, older messages get compressed into a summary so nothing important gets dropped.

---

## Directory Structure

```text
Flaude/
├── .github/
│   └── workflows/
│       ├── ci.yml              # Ruff format, lint, and MyPy on every push
│       └── codeql.yml          # Weekly CodeQL security scan
├── configs/                    # YAML config files (model params, paths, etc.)
├── src/
│   ├── core/
│   │   ├── agents/             # LLM chain definitions (chat, memory, summary)
│   │   ├── capabilities/       # Memory, RAG, and title generation logic
│   │   ├── tools/              # Web search, math, RAG tool, file search
│   │   └── workflow/           # LangGraph graph, node functions, state schema
│   ├── exception/              # Custom exception with file + line tracing
│   ├── infra/                  # DB connections, LLM init, CSS loader
│   ├── logger/                 # Rotating file + coloured console logger
│   └── ui/
│       ├── assets/             # Custom CSS styling (styles.css)
│       ├── components/         # Streamlit chat and sidebar components
│       ├── app.py              # Main Streamlit web application
│       └── state.py            # Session state initialization
├── tests/                      # Automated unit and integration test suite
├── main.py                     # Entry point launcher
├── pyproject.toml
├── run_tests.sh               # Curated test runner (supports --fix & --no-sync)
└── uv.lock
```

---

## Getting Started

### 1. Setup

Clone the repo and install everything with `uv`:

```bash
git clone https://github.com/sarveshmhadgut/Flaude.git
cd Flaude
uv sync
```

### 2. Configure

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required and optional configuration keys in `.env`:

```env
# Required: Google Gemini API Key for LLM Chat Agent & Embeddings
GOOGLE_API_KEY="your_google_api_key_here"

# Required: PostgreSQL Connection URI for LangGraph Checkpointing & Semantic Store
DB_URI="postgresql://username:password@localhost:5432/database_name"

# Optional: Currency Conversion Tool (https://www.exchangerate-api.com/)
EXCHANGE_RATE_KEY="your_exchangerate_api_key_here"

# Optional: LangSmith Tracing & Telemetry
LANGCHAIN_API_KEY="your_langsmith_api_key_here"
```

Flaude uses **PostgreSQL** via `DB_URI` for persistent session checkpointing (`PostgresSaver`) and semantic fact storage (`PostgresStore`). Point it to your running Postgres database instance. Local SQLite databases (`data/db/`) handle conversation metadata and thread title mappings automatically.

### 3. Run

Launch the application via the entry point launcher:

```bash
uv run python main.py
```

Alternatively, launch Streamlit directly:

```bash
uv run streamlit run src/ui/app.py
```

Open [http://localhost:8501](http://localhost:8501) and start chatting.
